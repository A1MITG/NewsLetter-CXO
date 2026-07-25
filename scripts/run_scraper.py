# scripts/run_scraper.py
import asyncio
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
load_dotenv()
from app.scraper.scraper import run_scraper

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


async def main():
    """A simple script to run the scraper and save the results for inspection."""
    logger.info("Running scraper...")
    articles = await run_scraper(tier='all')
    logger.info("Found %d articles.", len(articles))

    with open('scraped_articles.json', 'w') as f:
        json.dump(articles, f, indent=4)
    logger.info("Results saved to scraped_articles.json")

if __name__ == '__main__':
    asyncio.run(main())
