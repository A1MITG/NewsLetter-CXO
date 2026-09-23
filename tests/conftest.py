"""Shared pytest fixtures for the intelligence pipeline.

Every sprint tests against the real cached corpus rather than synthetic
fixtures. Synthetic data hides exactly the failures that matter here —
unparseable dates, missing descriptions, feed quirks — so the suite is
deliberately wired to instance/articles_cache.json.
"""
import json
import os
import pathlib

import pytest

# The app factory starts a background scrape thread; tests must not hit the
# network or race the cache file. Set before app.main is ever imported.
os.environ.setdefault("BACKGROUND_REFRESH", "0")
os.environ.setdefault("FETCH_ARTICLE_IMAGES", "0")
os.environ.setdefault("FETCH_LEADER_QUOTES", "0")

ROOT = pathlib.Path(__file__).resolve().parents[1]
CACHE = ROOT / "instance" / "articles_cache.json"
GOLD = ROOT / "data" / "gold_set.jsonl"

PRIORITIES = ("MUST_READ", "IMPORTANT", "WATCH", "BACKGROUND", "IGNORE")


@pytest.fixture(scope="session")
def cache_path():
    return CACHE


@pytest.fixture(scope="session")
def raw_cache(cache_path):
    if not cache_path.exists():
        pytest.skip("no instance/articles_cache.json — run the scraper first")
    return json.loads(cache_path.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def raw_articles(raw_cache):
    return raw_cache["articles"]


@pytest.fixture(scope="session")
def normalized(raw_articles):
    """Signals through Sprint 1. Session-scoped: the suite was re-running the
    whole pipeline per test, which is why it had crept to ~19s."""
    from app.intelligence.normalize import normalize_all
    return normalize_all(raw_articles)


@pytest.fixture(scope="session")
def enriched(raw_articles):
    """Signals through Sprint 4 — normalize, trust, freshness, domains."""
    from app.intelligence.domains import apply_all as domains_all
    from app.intelligence.freshness import apply_all as freshness_all
    from app.intelligence.normalize import normalize_all
    from app.intelligence.trust import apply_all as trust_all
    return domains_all(freshness_all(trust_all(normalize_all(raw_articles))))


@pytest.fixture(scope="session")
def gold():
    """Hand-labelled articles.

    Rows with an empty ``priority`` are skipped, so the suite stays green
    while the set is being filled in. Sprints 4+ can run without labels but
    cannot be *measured* without them.
    """
    if not GOLD.exists():
        return []
    rows = [
        json.loads(line)
        for line in GOLD.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return [r for r in rows if r.get("priority")]
