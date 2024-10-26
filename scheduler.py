import asyncio

from colorama import Fore
from logging_config import app_logger
from scrapper import scrape_search
# TODO: gui_queue in the import is not being accessed - check this
from gui import gui_queue, start_gui_thread, stop_gui_thread
from redis_utils import set_last_scrape, set_jobs_as_not_viewed, should_scrape_by_jobs_state, should_scrape_by_time

# from linkedin_scraper import linkedin_scrape_search, linkedin_login

logger = app_logger.getChild('scheduler')

async def one_time_scrape(query, location):
    found_new_jobs = await scrape_search(query=query, location=location, radius=25)
    return found_new_jobs

async def perform_scheduled_scrape(query, location, gui_queue, scraps_staggering_minutes):
    found_new_jobs = False

    logger.info(Fore.MAGENTA + f"Performing scrape for {query} in {location}")
    found_new_jobs = await scrape_search(query=query, location=location, radius=25)
    set_last_scrape(query, location)

    if found_new_jobs:
        set_jobs_as_not_viewed(query, location)
        gui_queue.put((f"New jobs found", f"New jobs found for {query} in {location}", query, location, scraps_staggering_minutes))

async def run_schedule(scrape_tasks, run_every_minutes, scraps_staggering_minutes, max_workers):
    start_gui_thread(max_workers)

    # TODO: note there might be a contradiction between the run_every_seconds and staggering_time_seconds
    run_every_seconds = run_every_minutes * 60
    staggering_time_seconds = scraps_staggering_minutes * 60 

    try:
        while True:
            for query, location in scrape_tasks:
                should_scrape_state = should_scrape_by_jobs_state(query, location)
                should_scrape_time = should_scrape_by_time(query, location, run_every_seconds)
                logger.info(Fore.YELLOW + f"Should scrape state: {should_scrape_state}, Should scrape time: {should_scrape_time}")

                if should_scrape_time and should_scrape_state:
                    await perform_scheduled_scrape(query, location, gui_queue, scraps_staggering_minutes)
                else:
                    logger.info(Fore.MAGENTA + f"Skipping scrape for {query} in {location}")
                
                await asyncio.sleep(staggering_time_seconds)
    finally:
        stop_gui_thread()

def start_scheduler(scrape_tasks, run_every_minutes, scraps_staggering_minutes, max_workers):
    # To run a coroutine. Runs the top level entry point
    asyncio.run(run_schedule(scrape_tasks, run_every_minutes, scraps_staggering_minutes, max_workers))

def run_one_time_scrape(query, location):
    asyncio.run(one_time_scrape(query, location))
