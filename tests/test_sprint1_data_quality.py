"""Sprint 1 exit tests (PRD §1 — Data Quality Foundation).

The contract: nothing the scraper captured may be discarded, and every
article published to the Command Center must carry full attribution.
"""
import json

import pytest

from app.intelligence.normalize import normalize, normalize_all, parse_date, publisher_for
from app.intelligence.schema import MAX_SUMMARY_CHARS, Signal


# ---------- nothing is discarded ----------

def test_raw_payload_is_preserved(raw_articles):
    for raw in raw_articles[:80]:
        sig = normalize(raw)
        if sig is None:
            continue
        for key, value in raw.items():
            assert sig.raw[key] == value, f"lost field {key!r} during normalize"


def test_scraped_date_and_image_survive(raw_articles):
    """The old build script dropped both. This is the regression guard."""
    sigs = normalize_all(raw_articles)
    assert any(s.published_at for s in sigs), "no dates survived normalize"
    assert any(s.image_url for s in sigs), "no images survived normalize"


# ---------- core shape ----------

def test_normalizer_produces_signals(raw_articles):
    sigs = normalize_all(raw_articles)
    assert sigs, "normalizer produced nothing"
    for s in sigs:
        assert isinstance(s, Signal)
        assert s.title and s.url and s.source.domain


def test_short_titles_rejected():
    assert normalize({"title": "Industry News", "url": "https://x.com/a"}) is None


def test_missing_url_rejected():
    assert normalize({"title": "A perfectly reasonable headline here", "url": ""}) is None


def test_duplicate_titles_collapse(raw_articles):
    sigs = normalize_all(raw_articles)
    titles = [s.title.lower() for s in sigs]
    assert len(titles) == len(set(titles)), "duplicate titles survived"


# ---------- attribution (user requirement: full credit to the publisher) ----------

def test_every_signal_is_attributed(raw_articles):
    for s in normalize_all(raw_articles):
        assert s.publisher, f"no publisher resolved for {s.source.domain}"
        assert s.canonical_url, "no canonical url for attribution"
        assert s.is_publishable(), f"not publishable: {s.title[:60]!r}"


def test_known_publishers_get_proper_names():
    assert publisher_for("livemint.com") == "Mint"
    assert publisher_for("economictimes.indiatimes.com") == "The Economic Times"
    assert publisher_for("feeds.bbci.co.uk") == "BBC News"     # parent-domain match
    assert publisher_for("theguardian.com") == "The Guardian"


def test_unknown_publisher_gets_readable_fallback():
    assert publisher_for("some-trade-journal.com") == "Some Trade Journal"
    assert publisher_for("") == ""


def test_summary_is_capped_for_fair_use():
    long_body = "x" * 5000
    sig = normalize({"title": "A headline of sufficient length here",
                     "url": "https://example.com/a", "summary": long_body})
    assert len(sig.summary) <= MAX_SUMMARY_CHARS


# ---------- dates ----------

def test_date_parsing_holds(raw_articles):
    sigs = normalize_all(raw_articles)
    dated = [s for s in sigs if s.published_at]
    ratio = len(dated) / len(sigs)
    assert ratio > 0.60, f"only {ratio:.0%} of articles have a parsed date"


def test_parses_rfc2822_and_iso():
    assert parse_date("Fri, 24 Jul 2026 16:54:17 +0000") is not None
    assert parse_date("2026-07-24T16:54:17Z") is not None
    assert parse_date("not a date") is None
    assert parse_date(None) is None


def test_parsed_dates_are_timezone_aware(raw_articles):
    for s in normalize_all(raw_articles):
        if s.published_at:
            assert s.published_at.tzinfo is not None


# ---------- explainability is live from Sprint 1 (§11) ----------

def test_unparseable_dates_are_explained(raw_articles):
    for s in normalize_all(raw_articles):
        if s.published_at is None and s.raw.get("date"):
            assert any(e["stage"] == "normalize" for e in s.explain), (
                "a dropped date left no trace")


def test_missing_summaries_are_explained(raw_articles):
    for s in normalize_all(raw_articles):
        if not s.summary:
            assert any("description" in e["reason"] for e in s.explain)


# ---------- serialisation ----------

def test_round_trip_is_json_safe(raw_articles):
    for s in normalize_all(raw_articles)[:25]:
        json.dumps(s.to_dict())


def test_enrichment_slots_start_empty(raw_articles):
    s = normalize_all(raw_articles)[0]
    assert s.domains == [] and s.entities == {} and s.events == []
    assert s.priority == "" and s.newsletter == {}


# ---------- Sprint 1 headline deliverable ----------

def test_summaries_are_populated(raw_articles):
    """Gated on the scraper patch + one fresh scrape.

    The RSS <description> is already in every feed; the parser simply never
    read it. Until a fresh scrape lands, the cached corpus has none.
    """
    sigs = normalize_all(raw_articles)
    have = sum(1 for s in sigs if s.summary)
    ratio = have / len(sigs)
    if ratio == 0:
        pytest.xfail("cached corpus predates the scraper patch — re-scrape to satisfy")
    assert ratio > 0.80, f"only {have}/{len(sigs)} ({ratio:.0%}) have summaries"
