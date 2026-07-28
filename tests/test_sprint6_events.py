"""Sprint 6 exit tests (PRD §6 — Event Detection).

Two contracts. Known events are detected, and terms of art in this corpus do
not masquerade as events — "war risk insurance" is a product, not a war.
"""
from app.intelligence.events import apply_all, detect, max_significance


def _types(title, summary=""):
    return {e["type"] for e in detect(title, summary)}


# ---------- detection of each major event class ----------

def test_acquisition():
    assert "ACQUISITION" in _types(
        "Mapfre to Acquire Safety Insurance for $1.54 Billion in Cash Deal")


def test_ipo():
    assert "IPO" in _types(
        "Anthropic may require employees to follow preset stock sale plans after IPO",
        "The initial public offering is expected next year.")


def test_funding():
    assert "FUNDING" in _types(
        "Elon Musk's Boring Company seeks funding at $20 billion valuation")


def test_executive_exit():
    assert "EXECUTIVE_EXIT" in _types("Union minister resigns amid cabinet reshuffle")


def test_executive_appointment():
    assert "EXECUTIVE_APPOINTMENT" in _types(
        "Berkley names Sarah Mitchell as CFO of its casualty unit")


def test_sanctions():
    assert "SANCTIONS" in _types("US imposes sanctions on shipping firms")


def test_cyber_attack():
    assert "CYBER_ATTACK" in _types("Insurer discloses ransomware attack on claims system")


def test_natural_disaster():
    assert "NATURAL_DISASTER" in _types("$1.1B cyclone damage exposes insurance gaps")


def test_interest_rate():
    assert "INTEREST_RATE" in _types("Central bank signals rate cut of 25 basis points")


def test_earnings():
    assert "EARNINGS" in _types("Munich Re reports preliminary Q2 net profit")


def test_conflict():
    assert "CONFLICT" in _types("Iran airstrike prompts ceasefire talks")


# ---------- veto: terms of art must not fire events ----------

def test_war_risk_insurance_is_not_a_conflict():
    """The exact phrase in this corpus. 'War risk' is an insurance product."""
    assert "CONFLICT" not in _types(
        "War Risk Insurance Surges for Southern Red Sea Voyages After Houthi Attacks")


def test_price_war_is_not_a_conflict():
    assert "CONFLICT" not in _types("Streaming price war intensifies as rivals cut fees")


def test_trade_war_routes_to_trade_not_conflict():
    t = _types("Trade war escalates as new tariffs are imposed")
    assert "CONFLICT" not in t
    assert "TRADE_ACTION" in t


# ---------- evidence discipline ----------

def test_single_weak_pattern_does_not_fire():
    """'deal' alone (weight 1) must not fire an acquisition."""
    assert "ACQUISITION" not in _types("A good deal for commuters on the new line")


def test_weak_launch_verb_alone_does_not_fire():
    assert "PRODUCT_LAUNCH" not in _types("Council launches consultation on parking")


def test_every_event_carries_evidence():
    for e in detect("Mapfre to acquire Safety Insurance in cash deal"):
        assert e["evidence"]
        for ev in e["evidence"]:
            assert ev["matched"] and ev["where"] in ("title", "summary")
            assert ev["weight"] > 0


def test_confidence_and_significance_bounded():
    for e in detect("US imposes sanctions after ransomware attack on port systems"):
        assert 0 < e["confidence"] <= 1.0
        assert 1 <= e["significance"] <= 5


# ---------- multiple events per article ----------

def test_article_can_carry_several_events():
    t = _types("Regulator fines insurer after data breach; CEO steps down")
    assert len(t) >= 2


def test_events_sorted_by_significance():
    events = detect("Regulator fines insurer after ransomware breach; CEO steps down")
    sigs = [e["significance"] for e in events]
    assert sigs == sorted(sigs, reverse=True)


def test_max_significance_helper():
    assert max_significance([]) == 0
    assert max_significance(detect("US imposes sanctions on shipping firms")) >= 4


# ---------- live corpus ----------

def test_detection_runs_clean_on_corpus(enriched):
    for s in apply_all(enriched):
        assert isinstance(s.events, list)


def test_corpus_yields_events(enriched):
    sigs = apply_all(enriched)
    with_events = [s for s in sigs if s.events]
    assert with_events, "no events detected in the entire corpus"
    ratio = len(with_events) / len(sigs)
    assert ratio < 0.85, f"{ratio:.0%} of articles fired an event — bar is too low"


def test_every_signal_is_traced(enriched):
    for s in apply_all(enriched):
        assert any(e["stage"] == "events" for e in s.explain)


def test_events_are_json_safe(enriched):
    import json
    for s in apply_all(enriched)[:30]:
        json.dumps(s.events)
