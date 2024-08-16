from scrapper import scrape_search
import asyncio

async def main():
    await scrape_search(query=" ", location=" ", radius=30)


# Use asyncio.run() here to start the event loop and run 'main'
asyncio.run(main())