# scripts/daily_linkedin_post.py
"""Run the newsletter pipeline and publish the daily brief to LinkedIn.

Usage:
  python scripts/daily_linkedin_post.py            # scrape, build brief, post
  python scripts/daily_linkedin_post.py --dry-run  # print the post, don't publish

Needs LINKEDIN_ACCESS_TOKEN and LINKEDIN_PERSON_URN in the environment
(one-time setup: python scripts/linkedin_auth.py).
"""
import argparse
import logging
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
load_dotenv()

from app.scraper.store import get_articles
from app.analysis.synthesis import synthesize_articles

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

API_VERSION = "202506"
POST_CHAR_LIMIT = 3000
LENSES = [
    'Macro & Geo-Political',
    'Regulatory & Compliance',
    'Economic & Market',
    'Digital, AI & Automation',
    'Operating Model & Talent',
]

# LinkedIn's Posts API treats these characters in `commentary` as formatting
# markers ("little text"); unescaped ones can get the post rejected. `#` is
# deliberately left out so hashtags still work.
LITTLE_TEXT_RESERVED = "\\|{}@[]()<>*_~"


def escape_commentary(text):
    for ch in LITTLE_TEXT_RESERVED:
        text = text.replace(ch, "\\" + ch)
    return text


def compose_post(brief):
    lines = [
        "SIGNAL — THE DAILY BRIEF",
        f"{brief['date']} · Know What Matters",
        "",
        brief["executive_takeaway"],
    ]
    section_count = 0
    for lens in LENSES:
        items = brief[lens][:2]
        if not items:
            continue
        section_count += 1
        lines.append("")
        lines.append(lens.upper())
        for item in items:
            lines.append(f"— {item['signal']}")
    if section_count == 0:
        lines += ["", "Quiet news day — no material CXO-level signals."]
    if brief["cxo_action_lens"]:
        lines.append("")
        lines.append("THE ACTION LENS")
        for action in brief["cxo_action_lens"][:3]:
            verb, _, rest = action.partition(":")
            lines.append(f"{verb.strip().upper()} — {rest.strip()}" if rest else f"— {action}")
    lines += ["", "#Insurance #CXO #Leadership #AI #RiskManagement"]
    return "\n".join(lines)[:POST_CHAR_LIMIT]


def post_to_linkedin(text):
    token = os.environ.get("LINKEDIN_ACCESS_TOKEN")
    author = os.environ.get("LINKEDIN_PERSON_URN")
    if not token or not author:
        raise SystemExit(
            "LINKEDIN_ACCESS_TOKEN / LINKEDIN_PERSON_URN not set. "
            "Run scripts/linkedin_auth.py first."
        )
    resp = requests.post(
        "https://api.linkedin.com/rest/posts",
        headers={
            "Authorization": f"Bearer {token}",
            "LinkedIn-Version": API_VERSION,
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json",
        },
        json={
            "author": author,
            "commentary": escape_commentary(text),
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        },
        timeout=30,
    )
    if resp.status_code == 201:
        logger.info("Posted to LinkedIn (id: %s)", resp.headers.get('x-restli-id', 'unknown'))
    elif resp.status_code == 401:
        raise SystemExit(
            "LinkedIn token expired or invalid — rerun scripts/linkedin_auth.py."
        )
    else:
        raise SystemExit(f"LinkedIn API error {resp.status_code}: {resp.text}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="print the post instead of publishing")
    args = parser.parse_args()

    logger.info("Running scraper (fresh, warms the daily cache)...")
    articles = get_articles(force_refresh=True)
    logger.info("Scraped %d articles.", len(articles))
    brief = synthesize_articles(articles)
    text = compose_post(brief)

    # Post content is the script's data output, not a log message — printed
    # directly (with framing) rather than routed through the logger.
    print("---- Post preview " + "-" * 30)
    print(text)
    print("-" * 48)

    if args.dry_run:
        logger.info("Dry run — not publishing.")
    else:
        post_to_linkedin(text)


if __name__ == "__main__":
    main()
