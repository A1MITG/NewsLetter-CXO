"""Sprint 2 exit tests (PRD §2 — Source Trust Framework)."""
import pytest

from app.intelligence.normalize import normalize_all
from app.intelligence.trust import WEIGHT_FLOOR, apply, apply_all, resolve, weight


# ---------- resolution never fails ----------

def test_every_real_source_resolves(raw_articles):
    """Every domain in the live corpus must resolve to a tier."""
    for s in apply_all(normalize_all(raw_articles)):
        assert s.source.tier in {"tier_1", "tier_2", "tier_3", "unknown"}
        assert 0.0 <= s.source.authority <= 1.0
        assert 0.0 <= s.source.independence <= 1.0


def test_unknown_source_never_crashes():
    info = resolve("some-outlet-nobody-configured.example")
    assert info["tier"] == "unknown"
    assert info["known"] is False


def test_empty_host_is_safe():
    assert resolve("")["tier"] == "unknown"
    assert resolve(None)["tier"] == "unknown"


def test_parent_domain_inheritance():
    """feeds.bbci.co.uk must inherit bbci.co.uk, not fall through to unknown."""
    assert resolve("feeds.bbci.co.uk")["tier"] == "tier_1"
    assert resolve("rss.economictimes.indiatimes.com")["tier"] == "tier_2"


# ---------- the two scores are genuinely orthogonal ----------

def test_authority_and_independence_are_independent():
    """An aggregator can be low-independence without being low-tier-by-accident."""
    aggregator = resolve("biztoc.com")
    trade = resolve("insurancejournal.com")
    assert aggregator["independence"] < trade["independence"]
    assert trade["authority"] > aggregator["authority"]


def test_trade_press_outranks_generalist_on_its_own_beat():
    """Insurance Journal on reinsurance should beat Times of India on reinsurance."""
    ij = resolve("insurancejournal.com")
    toi = resolve("timesofindia.indiatimes.com")
    assert weight(ij["authority"], ij["independence"]) > \
           weight(toi["authority"], toi["independence"])


def test_wire_services_rank_highest():
    reuters = resolve("reuters.com")
    assert reuters["tier"] == "tier_1"
    assert weight(reuters["authority"], reuters["independence"]) > 0.9


# ---------- PRD constraint: never suppress ----------

def test_trust_never_zeroes_a_story():
    """PRD §2: 'Trust Score must influence ranking but never completely
    suppress important information.'"""
    assert weight(0.0, 0.0) >= WEIGHT_FLOOR
    assert weight(0.0, 0.0) > 0.0


def test_weight_is_bounded_and_monotonic():
    assert weight(1.0, 1.0) == 1.0
    assert weight(0.0, 0.0) == WEIGHT_FLOOR
    assert weight(0.9, 0.5) > weight(0.4, 0.5)
    assert weight(0.5, 0.9) > weight(0.5, 0.4)


def test_off_domain_sports_sources_rank_last(raw_articles):
    """thebiglead.com arrives via NewsAPI. It must rank below every
    configured business source, without being excluded."""
    sports = resolve("thebiglead.com")
    business = resolve("livemint.com")
    w_sports = weight(sports["authority"], sports["independence"])
    assert w_sports < weight(business["authority"], business["independence"])
    assert w_sports >= WEIGHT_FLOOR       # penalised, not deleted


# ---------- explainability (§11) ----------

def test_every_trust_decision_is_traced(raw_articles):
    for s in apply_all(normalize_all(raw_articles)):
        assert any(e["stage"] == "trust" for e in s.explain), \
            f"no trust trace for {s.source.domain}"


def test_trace_carries_the_numbers(raw_articles):
    s = apply(normalize_all(raw_articles)[0])
    entry = next(e for e in s.explain if e["stage"] == "trust")
    for key in ("authority", "independence", "weight", "configured"):
        assert key in entry["evidence"]


# ---------- coverage of the live corpus ----------

def test_most_of_the_corpus_is_configured(raw_articles):
    """Unknown sources are allowed, but if most of the corpus is unknown the
    config has drifted away from the feeds."""
    sigs = apply_all(normalize_all(raw_articles))
    known = sum(1 for s in sigs if s.source.tier != "unknown")
    ratio = known / len(sigs)
    assert ratio > 0.90, f"only {ratio:.0%} of articles come from a configured source"
