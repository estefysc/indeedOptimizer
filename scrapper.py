import os
import json
import re
import time
import logging

from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Set
from urllib.parse import urlencode
from scrapfly import ScrapflyClient, ScrapeConfig
from ordered_set import OrderedSet
from dotenv import load_dotenv
from logging_config import app_logger
from redis_utils import save_job_to_redis, create_embeddings
from docker_utils import DockerEnvironment

@dataclass
class ScrappingJobConfig:
    query: str
    location: str
    radius: int
    # there's a page limit on indeed.com of 1000 results per search
    max_results: int = 1000
    directory: str = "scrapped_data"

load_dotenv()
api_key = os.getenv('API_KEY')
scrapfly = ScrapflyClient(key=api_key)

logger = app_logger.getChild('scraper')
logging.basicConfig(level=logging.INFO)

async def scrape_search(query: str, location: str, radius: int, max_results: int = 1000) -> bool:
    config = ScrappingJobConfig(query, location, radius, max_results)
    job_keys = set()
    results = {}

    try:
        os.makedirs(config.directory, exist_ok=True)

        logger.info(f"Scraping first page of search: query={query}, location={location}")
        data_first_page = await scrape_first_page(config)
        add_job_keys(data_first_page, job_keys, results)

        total_results = calculate_total_results(data_first_page, config.max_results)
        logger.info(f"Total results: {total_results}")

        number_of_pages = calculate_number_of_pages(total_results)
        logger.info(f"Total number of pages: {number_of_pages}. Scrapping now...")
        
        # For the highest precision, especially useful in measuring very short durations and benchmarking, use time.perf_counter()
        start_time = time.perf_counter()
        await scrape_remaining_pages(config, total_results, job_keys, results)
        save_results(results, config)    
        end_time = time.perf_counter()
        duration = end_time - start_time
        logger.info(f"Complete parsing took: {duration} seconds")
        
        new_keys = check_for_new_jobs(job_keys, config)
        logger.info(f"New Jobs: {len(new_keys)}")

        await create_report(new_keys, config)

        new_jobs_found = len(new_keys) > 0
        return new_jobs_found
    
    except Exception as e:
        logger.error(f"An error occurred during scraping: {e}")

async def scrape_first_page(config: ScrappingJobConfig) -> Dict:
    url = make_request_url(config.query, config.location, from_param="searchOnDesktopSerp")
    result = await scrapfly.async_scrape(ScrapeConfig(url, asp=True))
    return parse_search_page(result.content)

async def scrape_remaining_pages(config: ScrappingJobConfig, total_results: int, job_keys: Set[str], results: Dict):
    other_pages = generate_other_pages(config, total_results)
    # The concurrent_scrape() method in the Scrapfly Python SDK automatically manages concurrency up to the Scrapfly
    # account's concurrency limit.
    async for result in scrapfly.concurrent_scrape(other_pages):
        parsed_results = parse_search_page(result.content)
        add_job_keys(parsed_results, job_keys, results)

def calculate_total_results(data: Dict, max_results: int) -> int:
    total_results = sum(category["jobCount"] for category in data["meta"])
    return min(total_results, max_results)

def calculate_number_of_pages(total_results: int) -> int:
    # Adding 9 is a mathematical trick used to ensure that when you divide by 10, 
    # you effectively perform a ceiling division without needing to import additional functions or libraries. 
    # This addition makes sure that any remainder from the division (any number of results less than a full page) still 
    # counts as requiring an additional page. // = flooring operation
    number_of_pages = (total_results + 9) // 10
    return number_of_pages

def generate_other_pages(config: ScrappingJobConfig, total_results: int) -> List[ScrapeConfig]:
    # for offset in range(10, min(total_results, max_results), 10):
    #     url = make_page_url(query, location, radius, offset)
    #     config = ScrapeConfig(url, asp=True)
    #     other_pages.append(config)
    # The list comprehension below is equivalent to the code above
    return [
        ScrapeConfig(make_request_url(config.query, config.location, config.radius, offset=offset), asp=True)
        for offset in range(10, min(total_results, config.max_results), 10)
    ]

def save_results(results: Dict, config: ScrappingJobConfig):
    filename = f"{config.directory}/{config.query}_{config.location}_final_results.json"
    with open(filename, "w") as file:
        json.dump(results, file)

def make_request_url(query, location, radius=None, from_param=None, offset=None):
    # The first request to the Indeed search page only requires the query, location, and from parameter

    # Base parameters
    parameters = {"q": query, "l": location}
    
    # Add either `from` (for the first request) or `radius` and `start` (for paginated requests)
    if from_param is not None:
        parameters["from"] = from_param
    if radius is not None:
        parameters["radius"] = radius
    if offset is not None:
        parameters["start"] = offset
    
    url = "https://www.indeed.com/jobs?" + urlencode(parameters)
    
    logger.info(f"Scraping {url}")
    return url

# def add_job_keys(parsed_results, job_keys, results):
def add_job_keys(parsed_results: Dict, job_keys: Set[str], results: Dict):
    for result in parsed_results["results"]:
        job_key = result["jobkey"]
        if job_key not in job_keys:
            job_keys.add(job_key)
            results[job_key] = result

def parse_search_page(html: str):
    # This type of data is commonly known as hidden web data. 
    # It is the same data present on the web page but before it gets rendered in HTML.
    data = re.findall(r'window.mosaic.providerData\["mosaic-provider-jobcards"\]=(\{.+?\});', html)
    if not data:
        print("No data found with the regex pattern.")
        return {"results": [], "meta": []}  # Return empty data structure if nothing is found
    data = json.loads(data[0])
    return {
        "results": data["metaData"]["mosaicProviderJobCardsModel"]["results"],
        "meta": data["metaData"]["mosaicProviderJobCardsModel"]["tierSummaries"],
    }

def check_for_new_jobs(job_keys: Set[str], config: ScrappingJobConfig) -> Set[str]:
    old_jobkeys_filename = f"{config.directory}/{config.location}_jobkeys_old.json"
    new_jobkeys_filename = f"{config.directory}/{config.query}_{config.location}_new_keys.json"
    
    new_job_keys = set()
    old_job_keys = set()

    if os.path.exists(old_jobkeys_filename):
        with open(old_jobkeys_filename, "r") as file:
            old_job_keys = set(json.load(file))

    new_job_keys = job_keys - old_job_keys
    old_job_keys.update(new_job_keys)

    with open(old_jobkeys_filename, "w") as file:
        json.dump(list(old_job_keys), file)

    with open(new_jobkeys_filename, "w") as file:
        json.dump(list(new_job_keys), file)

    return new_job_keys

def formatCreateDate(create_date: str) -> str:
    formatted_date = int(create_date) / 1000
    date = datetime.fromtimestamp(formatted_date)
    formatted_date = date.strftime('%Y-%m-%d %H:%M:%S %Z')

    return formatted_date

async def create_report(new_keys: Set[str], config: ScrappingJobConfig):    
    report_filename = f"{config.directory}/{config.query}_{config.location}_report.json"
    full_scrap_filename = f"{config.directory}/{config.query}_{config.location}_final_results.json"
    report = []
    job_characteristics = OrderedSet([
        "applyCount",
        "company",
        "companyRating",
        "companyReviewCount",
        "createDate",
        "displayTitle",
        "estimatedSalary",
        "extractedSalary",
        "expired",
        "employerResponsive",
        "formattedLocation",
        "formattedRelativeTime",
        "hiringMultipleCandidatesModel",
        "jobCardRequirementsModel",
        "jobkey",
        "link",
        "newJob",
        "organicApplyStartCount",
        "pubDate",
        "remoteLocation",
        "remoteWorkModel",
        "taxonomyAttributes",
        "title",
        "salarySnippet",
        "urgentlyHiring"
    ])

    with open(full_scrap_filename, "r") as file:
        full_scrap = json.load(file)

    # TODO: Can this be refactored?
    for job_key, job_description in full_scrap.items():
        if job_key in new_keys:
            job_report = {}
            for key in job_characteristics:
                if key in job_description:
                    job_report[key] = job_description[key]
                    if key == "link":
                        description = await scrap_description_link(job_description[key])
                        job_report["jobDescription"] = description
                    if key == "createDate":
                        formattedCreateDate = formatCreateDate(job_description[key])
                        job_report["formattedCreateDate"] = formattedCreateDate
                    if key == "pubDate":
                        formattedCreateDate = formatCreateDate(job_description[key])
                        job_report["formattedPubDate"] = formattedCreateDate
                else:
                    job_report[key] = "Not provided"

            if DockerEnvironment.is_running_in_docker():
                save_job_to_redis(job_key, job_report)
                create_embeddings()

            report.append(job_report)
    
    with open(report_filename, "w") as file:
        json.dump(report, file)

async def scrap_description_link(link: str) -> str:
    url = "https://www.indeed.com" + link
    try:
        result = await scrapfly.async_scrape(ScrapeConfig(url, asp=True))
        target_div = result.selector.css('div#jobDescriptionText')
        
        if target_div:
            description_parts = target_div.css('*::text').getall()
            return clean_job_description(description_parts)
        else:
            logger.warning(f"Div not found for link: {link}")
            return "Job description not available."
    except Exception as e:
        logger.error(f"Error in scrap_description_link (scrapper.py) for link '{link}': {e}")
        return "Error retrieving job description."

def clean_job_description(description_parts: List[str]) -> str:
    return ' '.join(description_parts).replace("\n", "").replace("\u2019", "'").strip()