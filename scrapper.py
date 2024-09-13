import os
import json
import re
import time
import logging

from urllib.parse import urlencode
from scrapfly import ScrapflyClient, ScrapeConfig
from ordered_set import OrderedSet
from dotenv import load_dotenv
from logging_config import app_logger

load_dotenv()
api_key = os.getenv('API_KEY')
scrapfly = ScrapflyClient(key=api_key)

logger = app_logger.getChild('scraper')
logging.basicConfig(level=logging.INFO)

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

def add_job_keys(parsed_results, job_keys, results):
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

async def scrape_search(query: str, location: str, radius: int, max_results: int = 1000):
    job_keys = set()
    results = {}
    
    directory = "scrapped_data"
    os.makedirs(directory, exist_ok=True)
    final_results_filename = f"{directory}/{query}_{location}_final_results.json"
    old_jobkeys_filename = f"{directory}/{location}_jobkeys_old.json"
    report_filename = f"{directory}/{query}_{location}_report.json"
    new_jobkeys_filename = f"{directory}/{query}_{location}_new_keys.json"

    logger.info(f"Scraping first page of search: query={query}, location={location}")
    try:
        
        from_param = "searchOnDesktopSerp"
        result_first_page = await scrapfly.async_scrape(ScrapeConfig(make_request_url(
                                                        query, 
                                                        location, 
                                                        from_param),                                                         
                                                        asp=True))

        data_first_page = parse_search_page(result_first_page.content)
        add_job_keys(data_first_page, job_keys, results)

        total_results = sum(category["jobCount"] for category in data_first_page["meta"])
        logger.info(f"Total results: {total_results}")

        # there's a page limit on indeed.com of 1000 results per search
        if total_results > max_results:
            total_results = max_results
            
        # Adding 9 is a mathematical trick used to ensure that when you divide by 10, 
        # you effectively perform a ceiling division without needing to import additional functions or libraries. 
        # This addition makes sure that any remainder from the division (any number of results less than a full page) still 
        # counts as requiring an additional page. // = flooring operation
        number_of_pages = (total_results + 9) // 10
        logger.info(f"Total number of pages: {number_of_pages}. Scrapping now...")
        
        # for offset in range(10, min(total_results, max_results), 10):
        #     url = make_page_url(query, location, radius, offset)
        #     config = ScrapeConfig(url, asp=True)
        #     other_pages.append(config)
        # The list comprehension below is equivalent to the code above
        other_pages = [
            ScrapeConfig(make_request_url(query, location, radius, offset), asp=True)
            for offset in range(10, min(total_results, max_results), 10)
        ]

        # For the highest precision, especially useful in measuring very short durations and benchmarking, use time.perf_counter()
        start_time = time.perf_counter()

        # The concurrent_scrape() method in the Scrapfly Python SDK automatically manages concurrency up to the Scrapfly
        # account's concurrency limit.
        async for result in scrapfly.concurrent_scrape(other_pages):
            parsed_results = parse_search_page(result.content)
            add_job_keys(parsed_results, job_keys, results)

        with open(final_results_filename, "w") as file:
            json.dump(results, file)
        
        end_time = time.perf_counter()
        duration = end_time - start_time
        logger.info(f"Complete parsing took: {duration} seconds")
        
        new_keys = check_for_new_jobs(job_keys, old_jobkeys_filename, new_jobkeys_filename)
        logger.info(f"New Jobs: {len(new_keys)}")

        create_report(new_keys, final_results_filename, report_filename)
    except Exception as e:
        logger.error(f"An error occurred during scraping: {e}")

def check_for_new_jobs(job_keys: set, old_job_keys_file: str, new_job_keys_file: str):
    new_job_keys = set()
    old_job_keys = set()

    if os.path.exists(old_job_keys_file):
        with open(old_job_keys_file, "r") as file:
            old_job_keys = set(json.load(file))

    new_job_keys = job_keys - old_job_keys
    old_job_keys.update(new_job_keys)

    with open(old_job_keys_file, "w") as file:
        json.dump(list(old_job_keys), file)

    with open(new_job_keys_file, "w") as file:
        json.dump(list(new_job_keys), file)

    return new_job_keys

def create_report(new_job_keys: set, full_scrap_file: str, report_directory: str):
    report = []
    job_characteristics = OrderedSet([
        "applyCount",
        "company",
        "companyRating",
        "companyReviewCount",
        "createDate",
        "displayTitle",
        "estimatedSalary",
        "expired",
        "formattedLocation",
        "hiringMultipleCandidatesModel",
        "jobCardRequirementsModel",
        "jobkey",
        "link",
        "newJob",
        "rankingScoresModel",
        "remoteLocation",
        "remoteWorkModel",
        "taxonomyAttributes",
        "title",
        "urgentlyHiring"
    ])

    with open(full_scrap_file, "r") as file:
        full_scrap = json.load(file)

    for job_key, job_description in full_scrap.items():
        if job_key in new_job_keys:
            job_report = {}
            for key in job_characteristics:
                if key in job_description:
                    job_report[key] = job_description.get(key, "Not provided")
            report.append(job_report)
    
    with open(report_directory, "w") as file:
        json.dump(report, file)