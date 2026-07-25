# app/scraper/store.py
"""Daily article cache: scrape at most once per day, reuse everywhere.

The first request of the day (or a force_refresh) runs the full scrape and
writes the result to instance/articles_cache.json. Every later request that
day is served from the cache instantly. If a fresh scrape returns nothing
(sources down), the previous day's cache is served rather than an empty page.
"""
import asyncio
import json
import threading
from datetime import date
from pathlib import Path

from .scraper import run_scraper

CACHE_FILE = Path(__file__).resolve().parents[2] / 'instance' / 'articles_cache.json'
_lock = threading.Lock()


def get_articles(force_refresh=False):
    """Return today's articles, scraping only when the cache is stale."""
    with _lock:
        cached = _load()
        if not force_refresh and cached and cached.get('date') == date.today().isoformat():
            return cached['articles']
        articles = asyncio.run(run_scraper(tier='all'))
        if not articles and cached:
            return cached['articles']
        _save(articles)
        return articles


def _load():
    try:
        with open(CACHE_FILE, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def _save(articles):
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump({'date': date.today().isoformat(), 'articles': articles}, f)
