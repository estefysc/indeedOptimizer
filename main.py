from scrapper import scrape_search, scrape_google_jobs
import asyncio

async def main():
    await scrape_search(query="software engineer", location="sarasota", radius=25)

    # Approx +-2000 tokens
    # await scrape_search(query="software engineer", location="tampa", radius=25)

# Use asyncio.run() here to start the event loop and run 'main'
asyncio.run(main())