from scrapper import scrape_search
import asyncio

async def main():
    
    # await scrape_search(query="software", location="sarasota", radius=30)

    # await scrape_search(query="software", location="venice", radius=30)

    # await scrape_search(query="software developer", location="miami", radius=50)

    # await scrape_search(query="software engineer", location="tallahassee", radius=30)

    # await scrape_search(query="software engineer", location="bradenton", radius=25)

    # await scrape_search(query="software developer", location="nokomis", radius=50)

    # Approx +-2000 tokens
    # await scrape_search(query="software developer", location="tampa", radius=50)

    # +- 3000 tokens
    await scrape_search(query="software developer", location="remote", radius=20)

# Use asyncio.run() here to start the event loop and run 'main'
asyncio.run(main())