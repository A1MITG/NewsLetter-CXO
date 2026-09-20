"""Sprint 8 exit tests (PRD §8 — Executive Importance Classification).

STRUCTURAL tests assert the quota/floor mechanics. CALIBRATION tests measure
agreement with the gold set and are PROVISIONAL while labels are draft.
"""
import pytest

from app.intelligence.developments import apply_all as developments_all
from app.intelligence.developments import group as dev_group
from app.intelligence.entities import apply_all as entities_all
from app.intelligence.events import apply_all as events_all
from app.intelligence.impact import apply_all as impact_all
from app.intelligence.priority import (BANDS, classify_batch, distribution,
                                       top)


@pytest.fixture(scope="session")
def prioritised(enriched):
    # §10 sits between impact and priority in the real build. Stating it here
    # keeps this fixture deterministic: the shared `enriched` signals are
    # mutated in place, so leaving §10 out made the result depend on whether
    # a sprint-10 test had already run.
    return classify_batch(
        developments_all(impact_all(events_all(entities_all(enriched)))))


# ---------- structural ----------

def test_every_signal_gets_a_band(prioritised):
    for s in prioritised:
        assert s.priority in BANDS


def test_volume_is_controlled(prioritised):
    """PRD: 'Executives should never be overwhelmed by volume.'"""
    dist = distribution(prioritised)
    total = len(prioritised)
    assert dist["MUST_READ"] <= round(0.05 * total) + 1
    assert dist["MUST_READ"] + dist["IMPORTANT"] <= round(0.20 * total) + 2


def test_must_read_is_a_handful(prioritised):
    dist = distribution(prioritised)
    assert 0 < dist["MUST_READ"] <= 20, dist


def test_ranking_is_monotonic_among_leads(prioritised):
    """A higher score must never land in a lower band — among the articles
    that actually compete for one.

    Before §10 that was every eligible article. It no longer is: a follower
    carries its own, often high, score but is parked below the ranking because
    the story it reports is already represented by its lead. That is the point
    of §10, so followers are excluded here — and the second half of this test
    pins that they are the ONLY exception, which is the stronger claim.
    """
    order = {b: i for i, b in enumerate(BANDS)}
    eligible = [s for s in prioritised
                if s.freshness.get("is_current") and s.domains
                and s.priority != "IGNORE"]

    lead_ids = {id(members[0]) for members in dev_group(prioritised)}
    leads = [s for s in eligible if id(s) in lead_ids]
    leads.sort(key=lambda s: s.impact["score"], reverse=True)
    ranks = [order[s.priority] for s in leads]
    assert ranks == sorted(ranks), "a higher-scoring lead got a lower band"

    follower_band = "BACKGROUND"
    for s in eligible:
        if id(s) not in lead_ids:
            assert s.priority == follower_band, (
                f"a follower landed in {s.priority}, not {follower_band}: "
                f"{s.title}")


def test_floors_are_respected(prioritised):
    floors = {"MUST_READ": 60, "IMPORTANT": 50, "WATCH": 40}
    for s in prioritised:
        if s.priority in floors:
            assert s.impact["score"] >= floors[s.priority]


def test_stale_articles_are_hard_ignored(prioritised):
    for s in prioritised:
        if not s.freshness.get("is_current"):
            assert s.priority == "IGNORE"


def test_undomained_articles_are_hard_ignored(prioritised):
    for s in prioritised:
        if not s.domains:
            assert s.priority == "IGNORE"


def test_every_decision_is_traced(prioritised):
    for s in prioritised:
        assert any(e["stage"] == "priority" for e in s.explain)


def test_top_helper_returns_sorted(prioritised):
    chosen = top(prioritised)
    scores = [s.impact["score"] for s in chosen]
    assert scores == sorted(scores, reverse=True)


def test_empty_batch_is_safe():
    assert classify_batch([]) == []


# ---------- calibration (PROVISIONAL — draft labels) ----------

def _pairs(prioritised, gold):
    by = {s.title: s for s in prioritised}
    return [(row["priority"], by[row["title"]].priority)
            for row in gold if row["title"] in by]


def test_no_must_read_is_predicted_ignore(prioritised, gold):
    """The one confusion that is never acceptable: the most important story
    of the day filed as noise."""
    if not gold:
        pytest.skip("gold set not labelled")
    bad = [(g, p) for g, p in _pairs(prioritised, gold)
           if g == "MUST_READ" and p == "IGNORE"]
    assert not bad, f"{len(bad)} MUST_READ articles were classified IGNORE"


def test_adjacent_band_accuracy(prioritised, gold):
    """Exact agreement is a high bar for a five-way subjective split — humans
    disagree with themselves at the boundaries. Within-one-band is the
    meaningful measure."""
    if not gold:
        pytest.skip("gold set not labelled")
    order = {b: i for i, b in enumerate(BANDS)}
    pairs = _pairs(prioritised, gold)
    if not pairs:
        pytest.skip("no labelled overlap")
    within = sum(1 for g, p in pairs if abs(order[g] - order[p]) <= 1)
    ratio = within / len(pairs)
    assert ratio > 0.55, f"only {ratio:.0%} of predictions land within one band"
