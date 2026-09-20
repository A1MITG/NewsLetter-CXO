# scripts/build_command_center_data.py
"""Build the live data snapshot for the Command Center static deploy.

Run daily (alongside scripts/build_static_signals.py) to write:
    public/command_center_data.json

Maps the 6 real Signal categories from app/analysis/signals.py onto the
Command Center's existing engine ids. The other 9 tiles (Banking,
Manufacturing, Energy, Defence, Cyber, Supply Chain, Healthcare, Telecom,
Climate) have no scoring engine behind them yet, so they're written out
honestly as comingSoon rather than fabricated content.

Signal Executive is intentionally left out of this mapping — the Command
Center layout has no tile for it.
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

from app.scraper.store import get_articles, get_cache_date
from app.analysis.signals import synthesize_signals
from app.analysis.command_center import (build_engine_data, build_featured, build_hero_cards,
                                      build_pulse_cards)

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

PUBLIC_DIR = ROOT / 'public'

# Injected into the Flask template only: tells the page to read the live API
# instead of the static snapshot.
LIVE_URL_INJECT = '''<script>
    // Served by Flask: read live classified articles from the API, not the
    // prebuilt static snapshot. Must precede the main script block.
    window.CC_DATA_URL = "/api/command-center";
</script>
</head>'''

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

    signals_data = synthesize_signals(articles, data_date=data_date)
    by_name = {s['name']: s for s in signals_data['signals']}

    engine_data = build_engine_data(signals_data)
    by_title = {a.get('title'): a for a in articles}
    engine_data['_hero'] = build_hero_cards(engine_data, by_title)
    engine_data['_featured'] = build_featured(
        engine_data['_hero'], engine_data, by_title)
    engine_data['_pulse'] = build_pulse_cards(articles)
    # The static page shows the same freshness stamp as the live one; without
    # _meta it would render blank on the Vercel deploy.
    engine_data['_meta'] = {
        'data_date': data_date,
        'fetched_minutes_ago': 0,
        'stale_excluded': signals_data.get('stale_excluded', 0),
    }

    PUBLIC_DIR.mkdir(exist_ok=True)
    out_path = PUBLIC_DIR / 'command_center_data.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(engine_data, f, ensure_ascii=False)
    logger.info("Wrote %s", out_path)

    html_src = ROOT / 'app' / 'static' / 'command_center_source.html'
    source_html = html_src.read_text(encoding='utf-8')

    # Static deploy copy: no CC_DATA_URL, so the page falls back to the
    # committed command_center_data.json sitting beside it.
    html_out = PUBLIC_DIR / 'command_center.html'
    shutil.copy(html_src, html_out)
    logger.info("Wrote %s", html_out)

    # Flask template: same markup, plus the live API URL. Generated from the
    # same source so the served page and the static deploy cannot drift.
    template_out = ROOT / 'app' / 'templates' / 'command_center.html'
    template_html = source_html.replace('</head>', LIVE_URL_INJECT, 1)
    # Relative asset paths work for the static deploy (files sit beside the
    # page); Flask serves the same files from /static/, so rewrite them.
    template_html = template_html.replace('src="./img/', 'src="/static/img/')
    template_out.write_text(template_html, encoding='utf-8')
    logger.info("Wrote %s", template_out)


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--refresh', action='store_true',
                   help='re-scrape before building (overwrites the day cache)')
    main(**vars(p.parse_args()))