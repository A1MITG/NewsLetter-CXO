# app/scraper/scraper.py
import asyncio
import aiohttp
import random
import json
import os
from bs4 import BeautifulSoup
from .sources import TIER_1_SOURCES, TIER_2_SOURCES

# TODO: Implement a more sophisticated scraping mechanism.
# This could involve using a headless browser for JavaScript-heavy sites.
# Also, add error handling and logging.

async def fetch_newsapi_articles(session, api_key):
    """Fetch articles from NewsAPI with insurance keywords."""
    url = f"https://newsapi.org/v2/everything?q=insurance+OR+insurer+OR+reinsurance&language=en&sortBy=publishedAt&pageSize=20&apiKey={api_key}"
    try:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                articles = []
                for item in data.get('articles', []):
                    title = item.get('title', '').strip()
                    url = item.get('url', '')
                    date = item.get('publishedAt', '')
                    if title and url:
                        articles.append({
                            'title': title,
                            'url': url,
                            'date': date
                        })
                return articles
            else:
                print(f"NewsAPI error: {response.status}")
                return []
    except Exception as e:
        print(f"Error fetching NewsAPI: {e}")
        return []

async def fetch_html(session, url):
    """Fetch HTML content from a single URL."""
    # Add random delay to avoid rate limiting
    await asyncio.sleep(random.uniform(1, 3))
    try:
        async with session.get(url, timeout=10) as response:
            response.raise_for_status()
            return await response.text()
    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        print(f"Error fetching {url}: {e}")
        return None

async def scrape_source(session, url):
    """Scrape a single source for article links and titles."""
    html = await fetch_html(session, url)
    if not html:
        return []

    articles = []
    if url.endswith('.rss') or url.endswith('.xml') or 'rss' in url.lower() or 'feed' in url.lower():
        # Parse as RSS/XML
        soup = BeautifulSoup(html, 'xml')
        for item in soup.find_all(['item', 'entry']):
            title_tag = item.find('title')
            link_tag = item.find('link')
            date_tag = item.find('pubDate') or item.find('published') or item.find('updated')
            if title_tag and link_tag:
                title = title_tag.text.strip()
                link = link_tag.get('href') or link_tag.text.strip()
                if not link.startswith('http'):
                    link = url.rsplit('/', 1)[0] + '/' + link
                date = date_tag.text.strip() if date_tag else None
                if title and len(title) > 10:
                    articles.append({
                        'title': title,
                        'url': link,
                        'date': date
                    })
    else:
        # Parse as HTML
        soup = BeautifulSoup(html, 'html.parser')
        # Basic HTML scraping: find article links
        count = 0
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            title = a_tag.text.strip()
            if title and len(title) > 10 and len(title) < 200 and ('news' in href.lower() or 'article' in href.lower() or '/202' in href) and not any(word in title.lower() for word in ['home', 'about', 'contact', 'privacy', 'terms']):
                full_url = href if href.startswith('http') else url.rstrip('/') + '/' + href.lstrip('/')
                articles.append({
                    'title': title,
                    'url': full_url,
                    'date': None
                })
                count += 1
                if count >= 10:  # Limit to 10 per site
                    break
    return articles

async def run_scraper(tier='all'):
    """Run the scraper for the specified tier of sources."""
    sources_to_scan = []
    if tier == 'tier1' or tier == 'all':
        for category in TIER_1_SOURCES.values():
            sources_to_scan.extend(category)
    if tier == 'tier2' or tier == 'all':
        for category in TIER_2_SOURCES.values():
            sources_to_scan.extend(category)

    all_articles = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    async with aiohttp.ClientSession(headers=headers) as session:
        tasks = [scrape_source(session, url) for url in sources_to_scan]
        results = await asyncio.gather(*tasks)
        for articles in results:
            all_articles.extend(articles)

        # Add NewsAPI articles if key is available
        news_api_key = os.environ.get('NEWS_API_KEY', '')
        if news_api_key:
            news_articles = await fetch_newsapi_articles(session, news_api_key)
            all_articles.extend(news_articles)

    # Deduplicate articles by URL
    all_articles = list({article['url']: article for article in all_articles if article.get('url')}.values())

    return all_articles
