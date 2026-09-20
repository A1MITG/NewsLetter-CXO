# scripts/build_static_signals.py
"""Build a static, self-contained deploy of the Signals page for Vercel.

Run daily by .github/workflows/build-signals.yml (or manually). Scrapes
fresh, classifies into the six Signals, and writes:
    public/index.html   the real signals.html template, rendered once
    public/signals.json  the data it fetches (in place of a live API)
    public/signal.css    the page's stylesheet

Vercel then serves public/ as static files — no Python runtime, no
filesystem-persistence risk, no request-time scraping. Re-run this (via the
workflow's daily schedule or its manual "Run workflow" button) to refresh
the published snapshot.
"""
import json
import logging
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv()

from flask import render_template

from app.main import app
from app.scraper.store import get_articles, get_cache_date
from app.analysis.signals import synthesize_signals

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

PUBLIC_DIR = ROOT / 'public'

# The live page fetches its data from the Flask API, links its stylesheet
# through Flask's /static/ route, and links back to the Daily Brief. None
# of those exist in this standalone static deploy.
LIVE_API_FETCH = "fetch('/api/signals')"
STATIC_JSON_FETCH = "fetch('./signals.json')"
FLASK_STATIC_CSS = '<link rel="stylesheet" href="/static/signal.css">'
FLAT_STATIC_CSS = '<link rel="stylesheet" href="./signal.css">'
DAILY_BRIEF_LINK = '<div class="utility">\n        <span id="last-updated"></span>\n        <a href="/">&larr; DAILY BRIEF</a>\n    </div>'
STATIC_UTILITY = '<div class="utility">\n        <span id="last-updated"></span>\n    </div>'


# A build does not re-scrape by default. store.py already scrapes at most
# once a day; forcing a refresh here meant every build replaced the single
# cache slot, so two surfaces built minutes apart could rest on two different
# article sets. Pass --refresh when you actually want new articles.
def main(refresh=False):
    articles = get_articles(force_refresh=refresh)
    data_date = get_cache_date()
    logger.info("%d articles from the %s cache%s.",
                len(articles), data_date or "undated",
                " (re-scraped)" if refresh else "")

    data = synthesize_signals(articles, data_date=data_date)

    PUBLIC_DIR.mkdir(exist_ok=True)

    with open(PUBLIC_DIR / 'signals.json', 'w', encoding='utf-8') as f:
        json.dump(data, f)
    logger.info("Wrote %s", PUBLIC_DIR / 'signals.json')

    shutil.copy(ROOT / 'app' / 'static' / 'signal.css', PUBLIC_DIR / 'signal.css')
    logger.info("Wrote %s", PUBLIC_DIR / 'signal.css')

    with app.test_request_context():
        html = render_template('signals.html')

    if (LIVE_API_FETCH not in html or DAILY_BRIEF_LINK not in html
            or FLASK_STATIC_CSS not in html):
        raise RuntimeError(
            "signals.html no longer matches the expected markup — update "
            "the substitutions in this script to match the new template."
        )
    html = html.replace(LIVE_API_FETCH, STATIC_JSON_FETCH)
    html = html.replace(FLASK_STATIC_CSS, FLAT_STATIC_CSS)
    html = html.replace(DAILY_BRIEF_LINK, STATIC_UTILITY)

    (PUBLIC_DIR / 'index.html').write_text(html, encoding='utf-8')
    logger.info("Wrote %s", PUBLIC_DIR / 'index.html')


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--refresh', action='store_true',
                   help='re-scrape before building (overwrites the day cache)')
    main(**vars(p.parse_args()))
