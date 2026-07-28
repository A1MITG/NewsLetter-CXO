"""Shared pytest fixtures for the intelligence pipeline.

Every sprint tests against the real cached corpus rather than synthetic
fixtures. Synthetic data hides exactly the failures that matter here —
unparseable dates, missing descriptions, feed quirks — so the suite is
deliberately wired to instance/articles_cache.json.
"""
import json
import pathlib

import pytest

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
