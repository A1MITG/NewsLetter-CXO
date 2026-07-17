# scripts/run_scraper.py
import asyncio
import json
from dotenv import load_dotenv
load_dotenv()
from app.scraper.scraper import run_scraper

async def main():
    """
    A simple script to run the scraper and print the results.
    """
    print("Running scraper...")
    articles = await run_scraper(tier='all')
    print(f"Found {len(articles)} articles.")

    # Save to a file for inspection
    with open('scraped_articles.json', 'w') as f:
        json.dump(articles, f, indent=4)
    print("Results saved to scraped_articles.json")

if __name__ == '__main__':
    asyncio.run(main())
