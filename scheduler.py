import asyncio
from scrapper import scrape_search
from redis_utils import set_last_scrape, set_jobs_as_not_viewed, should_scrape_by_jobs_state, should_scrape_by_time

async def scheduled_scrape(query, location, interval_minutes):
    seconds = interval_minutes * 60
    while True:
        # should_scrape_state = should_scrape_by_jobs_state(query, location)
        should_scrape_time = should_scrape_by_time(query, location, seconds)

        if should_scrape_time:
            found_new_jobs = await scrape_search(query=query, location=location, radius=25)
            set_last_scrape(query, location)

        if found_new_jobs:
            set_jobs_as_not_viewed(query, location)

        
        await asyncio.sleep(seconds)

async def run_schedule():
    run_every_minutes = 5
    scrape1 = asyncio.create_task(scheduled_scrape("software_development", "sarasota", run_every_minutes))
    
    # the next scheduled scrap will run 15 minutes later
    await asyncio.sleep(1 * 60)
    scrape2 = asyncio.create_task(scheduled_scrape("software_engineer", "sarasota", run_every_minutes))
    
    await asyncio.gather(scrape1, scrape2)

def start_scheduler():
    asyncio.run(run_schedule())