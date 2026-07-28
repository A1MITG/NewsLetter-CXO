"""Sprint 4 exit tests (PRD §4 — Domain Detection).

The headline contract: no domain may be assigned on the strength of a single
non-decisive keyword. That defect produced 39% of live classifications and is
the direct cause of the known false positives asserted below.
"""
from app.intelligence.domains import (apply_all, classified_only, classify,
                                      score_domains)
from app.intelligence.normalize import normalize_all


# ---------- the defect this sprint closes ----------

def test_single_weak_keyword_does_not_classify():
    """'Paul J. Stock named president...' was filed under Business on the
    strength of the person's surname."""
    r = classify("Paul J. Stock named president of Berkley's Carolina Casualty")
    assert r["primary"] != "economy", "surname 'Stock' still classifies as markets"


def test_data_center_alone_is_not_an_ai_story():
    """'PG&E's Data Center Pipeline Surges' was filed under AI."""
    r = classify("PG&E's Data Center Pipeline Surges in Second Quarter")
    assert r["primary"] != "ai", "'data center' alone still classifies as AI"


def test_bare_insurance_mention_is_not_enough():
    r = classify("2026 Tax Facts on Insurance & Employee Benefits (Volumes 1 & 2)")
    assert r["primary"] is None or r["primary"] != "insurance" or \
        len(r["domains"][0]["evidence"]) >= 2


def test_decisive_keyword_still_classifies_alone():
    """A weight-4 term is definitive by itself — the rule must not over-correct."""
    r = classify("Reinsurance renewals firm up ahead of the January treaty season")
    assert r["primary"] == "insurance"


def test_single_keyword_rate_is_low_on_live_corpus(raw_articles):
    """Sprint 4 exit criterion: down from 39% to under 10%."""
    sigs = classified_only(apply_all(normalize_all(raw_articles)))
    assert sigs, "nothing classified at all — the bar is too high"
    single = sum(1 for s in sigs if len(s.domains[0]["evidence"]) == 1)
    ratio = single / len(sigs)
    assert ratio < 0.10, f"{ratio:.0%} of classifications rest on one keyword"


# ---------- multi-domain (PRD: do not force a single category) ----------

def test_article_can_hold_multiple_domains():
    r = classify(
        "Insurer deploys generative AI underwriting platform after $2bn acquisition",
        "The insurtech acquisition gives the reinsurer machine learning capability.")
    assert len(r["domains"]) >= 2, "multi-domain never triggers"
    assert r["domains"][0]["role"] == "primary"
    assert all(d["role"] == "secondary" for d in r["domains"][1:])


def test_multi_domain_occurs_on_live_corpus(raw_articles):
    sigs = classified_only(apply_all(normalize_all(raw_articles)))
    multi = [s for s in sigs if len(s.domains) > 1]
    assert multi, "no article in the whole corpus got a secondary domain"


def test_secondary_must_clear_the_ratio():
    r = classify("Reinsurance renewals firm up ahead of the treaty season")
    if len(r["domains"]) > 1:
        top = r["domains"][0]["score"]
        for d in r["domains"][1:]:
            assert d["score"] >= top * 0.5


# ---------- evidence and confidence ----------

def test_every_assignment_carries_evidence(raw_articles):
    for s in classified_only(apply_all(normalize_all(raw_articles))):
        for d in s.domains:
            assert d["evidence"], f"{d['domain']} assigned with no evidence"
            for e in d["evidence"]:
                assert e["keyword"] and e["weight"] > 0
                assert e["where"] in ("title", "summary")


def test_confidence_is_bounded(raw_articles):
    for s in classified_only(apply_all(normalize_all(raw_articles))):
        for d in s.domains:
            assert 0.0 < d["confidence"] <= 1.0


def test_summary_contributes_evidence(raw_articles):
    """Sprint 1 unlocked summaries; Sprint 4 must actually use them."""
    sigs = classified_only(apply_all(normalize_all(raw_articles)))
    from_summary = sum(1 for s in sigs for d in s.domains
                       for e in d["evidence"] if e["where"] == "summary")
    assert from_summary > 0, "summaries are being ignored by the classifier"


# ---------- taxonomy routing ----------

def test_every_domain_routes_to_engine_and_signal(raw_articles):
    for s in classified_only(apply_all(normalize_all(raw_articles))):
        assert s.engine_id and s.signal_name
        for d in s.domains:
            assert d["engine"] and d["signal"] and d["display"]


def test_executive_now_has_an_engine():
    """Previously scored then discarded — the Command Center had no tile."""
    r = classify("Chief executive officer steps down; board names successor",
                 "The c-suite succession follows a boardroom review.")
    if r["primary"] == "executive":
        assert r["domains"][0]["engine"] == "executive"


def test_gulf_context_still_vetoes_gcc():
    """Regression guard on the legacy disambiguation."""
    r = classify("Saudi Arabia and UAE lead GCC summit on energy security")
    assert r["primary"] != "gcc"


# ---------- explainability (§11) ----------

def test_every_signal_is_traced(raw_articles):
    for s in apply_all(normalize_all(raw_articles)):
        assert any(e["stage"] == "domains" for e in s.explain)


def test_unclassified_articles_explain_why(raw_articles):
    for s in apply_all(normalize_all(raw_articles)):
        if not s.domains:
            entry = next(e for e in s.explain if e["stage"] == "domains")
            assert "evidence bar" in entry["reason"]
