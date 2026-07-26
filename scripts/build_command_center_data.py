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

from app.scraper.store import get_articles
from app.analysis.signals import synthesize_signals

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

PUBLIC_DIR = ROOT / 'public'

# Signal name -> (Command Center engine id, display name)
SIGNAL_TO_ENGINE = {
    'Signal Global': ('global', 'Global Affairs'),
    'Signal Business': ('economy', 'Economy, Business & Markets'),
    'Signal AI': ('ai', 'AI, Technology & Innovation'),
    'Signal GCC': ('gcc', 'GCC & Enterprise Technology'),
    'Signal Insurance': ('insurance', 'Insurance & Financial Services'),
}

# Engines with no scoring logic yet — written out honestly, not fabricated.
COMING_SOON_ENGINES = {
    'banking': 'Banking',
    'manufacturing': 'Manufacturing',
    'energy': 'Energy',
    'defence': 'Defence',
    'cyber': 'Cyber Intelligence',
    'supplychain': 'Supply Chain',
    'healthcare': 'Healthcare',
    'telecom': 'Telecom & Digital Infrastructure',
    'climate': 'Climate & Sustainability',
}
COMING_SOON_NOTE = (
    "No scoring engine built for this domain yet — it isn't classifying "
    "real articles today. Planned as a future configurable Intelligence Domain."
)


def main():
    logger.info("Scraping fresh articles for the Command Center live build...")
    articles = get_articles(force_refresh=True)
    logger.info("Scraped %d articles.", len(articles))

    signals_data = synthesize_signals(articles)
    by_name = {s['name']: s for s in signals_data['signals']}

    engine_data = {}
    for signal_name, (engine_id, display_name) in SIGNAL_TO_ENGINE.items():
        signal = by_name.get(signal_name, {})
        engine_data[engine_id] = {
            'name': display_name,
            'articles': [
                {'title': a['title'], 'url': a['url']}
                for a in signal.get('articles', [])
            ],
        }

    for engine_id, display_name in COMING_SOON_ENGINES.items():
        engine_data[engine_id] = {
            'name': display_name,
            'comingSoon': True,
            'note': COMING_SOON_NOTE,
        }

    PUBLIC_DIR.mkdir(exist_ok=True)
    out_path = PUBLIC_DIR / 'command_center_data.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(engine_data, f, ensure_ascii=False)
    logger.info("Wrote %s", out_path)

    html_src = ROOT / 'app' / 'static' / 'command_center_source.html'
    html_out = PUBLIC_DIR / 'command_center.html'
    shutil.copy(html_src, html_out)
    logger.info("Wrote %s", html_out)


if __name__ == '__main__':
    main()