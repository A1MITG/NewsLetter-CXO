# app/scraper/store.py
"""Article cache with a time-to-live.

A scrape runs when the cache is older than CACHE_TTL_MINUTES (or on a
force_refresh); every request inside that window is served from disk. The TTL
replaced a calendar-day check: a once-a-day cache meant news breaking after
the first visitor of the day could not appear until the next day, so an
afternoon reader saw a morning snapshot stamped "today".

If a fresh scrape returns nothing (sources down), the previous cache is served
rather than an empty page.
"""
import asyncio
import json
import logging
import os
import threading
import time
from datetime import date, datetime, timezone
from pathlib import Path

from .scraper import run_scraper

logger = logging.getLogger(__name__)

CACHE_FILE = Path(__file__).resolve().parents[2] / 'instance' / 'articles_cache.json'
_lock = threading.Lock()

# How long a scrape stays warm. Short enough that a reader opening the page in
# the afternoon sees the afternoon's news; long enough that a burst of traffic
# does not hammer every upstream feed. Override with CACHE_TTL_MINUTES.
CACHE_TTL_MINUTES = int(os.environ.get('CACHE_TTL_MINUTES', '30'))

# A lazy TTL only refreshes when somebody asks, so the first visitor after a
# quiet night pays for the scrape and sees a spinner. The background refresher
# keeps the cache warm on a timer instead, so every reader gets a warm hit.
# Set BACKGROUND_REFRESH=0 to disable (tests, one-off scripts, CI).
BACKGROUND_REFRESH = os.environ.get('BACKGROUND_REFRESH', '1') != '0'
_refresher_started = False


def get_articles(force_refresh=False):
    """Return the current articles, scraping when the cache has expired."""
    with _lock:
        cached = _load()
        if not force_refresh and _is_fresh(cached):
            return cached['articles']
        articles = asyncio.run(run_scraper(tier='all'))
        if not articles and cached:
            return cached['articles']
        _save(articles)
        return articles


def get_cached_articles():
    """The cached articles as they stand, never scraping; [] with no cache.

    For pages a reader should not wait on: the background refresher keeps
    the cache warm, and the page states when its articles were fetched.
    """
    return (_load() or {}).get('articles', [])


def _is_fresh(cached):
    """True when the cache is inside its TTL."""
    if not cached:
        return False
    fetched = cached.get('fetched_at')
    if not fetched:
        # Pre-TTL cache files only carry a date. Treat same-day as fresh so an
        # upgrade does not force a scrape, but never trust an older one.
        return cached.get('date') == date.today().isoformat()
    try:
        ts = datetime.fromisoformat(fetched)
    except ValueError:
        return False
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    age_minutes = (datetime.now(timezone.utc) - ts).total_seconds() / 60
    return age_minutes < CACHE_TTL_MINUTES


def cache_age_minutes():
    """Minutes since the cached articles were fetched, or None."""
    cached = _load()
    fetched = (cached or {}).get('fetched_at')
    if not fetched:
        return None
    try:
        ts = datetime.fromisoformat(fetched)
    except ValueError:
        return None
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - ts).total_seconds() / 60


def get_cache_date():
    """The date of the articles currently cached, or None when there is none.

    Anything built from this cache must date itself by THIS, not by when the
    build ran — otherwise a Sunday rebuild stamps Friday's news as today's.
    """
    cached = _load()
    return (cached or {}).get('date')


def _load():
    try:
        with open(CACHE_FILE, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def _save(articles):
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump({'date': date.today().isoformat(),
                   'fetched_at': datetime.now(timezone.utc).isoformat(),
                   'articles': articles}, f)


def start_background_refresh():
    """Keep the cache warm on a timer, so no reader waits for a scrape.

    Idempotent. Runs as a daemon thread so it never holds up interpreter
    shutdown. Call it from the first request rather than at import time: the
    dev server imports the app in both the reloader parent and its child, and
    an import-time start would leave an orphan thread scraping in the parent.
    """
    global _refresher_started
    if _refresher_started or not BACKGROUND_REFRESH:
        return
    _refresher_started = True

    interval = max(60, CACHE_TTL_MINUTES * 60)

    def loop():
        while True:
            try:
                if not _is_fresh(_load()):
                    logger.info("Background refresh: cache expired, re-scraping.")
                    get_articles()
                    logger.info("Background refresh: done (%d articles).",
                                len(_load().get('articles', [])))
            except Exception:
                # A refresh failure must never kill the thread — the next tick
                # tries again, and readers keep getting the last good cache.
                logger.exception("Background refresh failed; will retry.")
            time.sleep(interval)

    threading.Thread(target=loop, name='cache-refresher', daemon=True).start()
    logger.info("Background refresh every %d min (TTL %d min).",
                interval // 60, CACHE_TTL_MINUTES)
