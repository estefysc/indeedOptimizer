import json
import os
import re
import time
from typing import List
from urllib.parse import urlencode
from scrapfly import ScrapflyClient, ScrapeConfig
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('API_KEY')
scrapfly = ScrapflyClient(key=api_key)

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
    def make_page_url(offset):
        # parameters = {"q": query, "l": location, "filter": 0, "start": offset}
        parameters = {"q": query, "l": location, "radius": radius, "filter": 0, "start": offset}
        url = "https://www.indeed.com/jobs?" + urlencode(parameters)
        print(f"Scraping {url}")
        return url
    
    directory = "scrapped_data"
    final_results_filename = f"{directory}/{query}_{location}_final_results.json"
    old_jobkeys_filename = f"{directory}/{location}_jobkeys_old.json"
    report_filename = f"{directory}/{query}_{location}_report.json"
    new_jobkeys_filename = f"{directory}/{query}_{location}_new_keys.json"

    print(f"scraping first page of search: {query=}, {location=}")
    # ASP = Anti Scraping Protection
    result_first_page = await scrapfly.async_scrape(ScrapeConfig(make_page_url(0), asp=True))
    data_first_page = parse_search_page(result_first_page.content)
    for result in data_first_page["results"]:
        job_key = result["jobkey"]
        if job_key not in job_keys:
            job_keys.add(job_key)
            results[job_key] = result  

    total_results = sum(category["jobCount"] for category in data_first_page["meta"])
    print (f"total results before conversion: {total_results}")

    # there's a page limit on indeed.com of 1000 results per search
    if total_results > max_results:
        total_results = max_results
        
    # Adding 9 is a mathematical trick used to ensure that when you divide by 10, 
    # you effectively perform a ceiling division without needing to import additional functions or libraries. 
    # This addition makes sure that any remainder from the division (any number of results less than a full page) still 
    # counts as requiring an additional page. // = flooring operation
    number_of_pages = (total_results + 9) // 10
    print(f"Total number of pages: {number_of_pages}")
    print(f"scraping remaining {number_of_pages - 1} pages")
    
    other_pages = [
        ScrapeConfig(make_page_url(offset), asp=True)
        for offset in range(10, min(total_results, max_results), 10)
        # for offset in range(10, 20, 10)
    ]
    print(f"The size of other_pages is {len(other_pages)}")

    # For the highest precision, especially useful in measuring very short durations and benchmarking, use time.perf_counter()
    start_time = time.perf_counter()
    # TODO: add try block
    async for result in scrapfly.concurrent_scrape(other_pages):
        other_pages_results = parse_search_page(result.content)
        for result in other_pages_results["results"]:
            job_key = result["jobkey"]
            if job_key not in job_keys:
                job_keys.add(job_key)
                results[job_key] = result  

    with open(final_results_filename, "w") as file:
        json.dump(results, file)

    print(f"The final length of job_keys is {len(job_keys)}")
    print(job_keys)
    end_time = time.perf_counter()
    duration = end_time - start_time
    print(f"Complete parsing took: {duration} seconds")
    new_keys, old_keys = check_for_new_jobs(job_keys, old_jobkeys_filename, new_jobkeys_filename)
    create_report(new_keys, final_results_filename, report_filename)
    replace_old_jobkeys_file(new_keys, old_keys, old_jobkeys_filename)

def check_for_new_jobs(job_keys: list, old_job_keys_file: str, new_job_keys_file: str):
    new_job_keys = []
    with open(old_job_keys_file, "r") as file:
        old_job_keys = json.load(file)

    for key in job_keys:
        if key not in old_job_keys and key not in new_job_keys:
            new_job_keys.append(key)

    with open(new_job_keys_file, "w") as file:
        json.dump(new_job_keys, file)

    return new_job_keys, old_job_keys

def replace_old_jobkeys_file(newJobs_keys: list, oldJobs_keys: list, oldJobs_directory: str):
    job_keys = oldJobs_keys + newJobs_keys
    with open(oldJobs_directory, "w") as file:
            json.dump(job_keys, file)

def create_report(new_job_keys: list, full_scrap_file: str, report_directory: str):
    report = []
    job_characteristics = [
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
    ]
    with open(full_scrap_file, "r") as file:
        full_scrap = json.load(file)

    # From the full scrap, get the results marked by the new_job_keys
    for job_key, job_description in full_scrap.items():
        if job_key in new_job_keys:
            report.append({key: job_description.get(key, "Not provided") for key in job_characteristics})
    
    with open(report_directory, "w") as file:
        json.dump(report, file)

# this is the url of the actual job page https://www.indeed.com/viewjob?jk=01fa92a46c94fd1a
#TODO: check if spam, check time creation of post, add filter not show certain company

# base url for jobs?
# https://www.google.com/search?client=firefox-b-1-d&q=software+sarasota&ibp=htl;jobs
# 3 days ago
# https://www.google.com/search?client=firefox-b-1-d&q=software+sarasota&ibp=htl;jobs&htichips=date_posted:3days&htischips=date_posted;3days
# https://www.google.com/search?client=firefox-b-1-d&q=software+sarasota&ibp=htl;jobs&sa=X&ved=2ahUKEwi57ZDkuoOGAxXat4QIHeRRB50QutcGKAF6BAgiEAQ#fpstate=tldetail&htivrt=jobs&htichips=date_posted:3days&htischips=date_posted;3days&htilrad=321.868&htidocid=97HobkDIPziCaxHeAAAAAA%3D%3D

async def scrape_google_jobs():

    def make_page_url():
        url = "https://www.google.com/search?client=firefox-b-1-d&q=software+sarasota&ibp=htl;jobs&htichips=date_posted:3days&htischips=date_posted;3days"
        print(f"Scraping {url}")
        return url
    
    result_first_page = await scrapfly.async_scrape(ScrapeConfig(make_page_url(), asp=True))
    print(result_first_page.content)