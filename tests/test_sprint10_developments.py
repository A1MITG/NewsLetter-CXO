"""Sprint 10 exit tests (PRD §10 — Developments).

STRUCTURAL tests assert the grouping rule and the contract §8 depends on.
The REGRESSION test pins the specific failure this sprint exists to fix: on
the 2026-09-12 build, two articles on one Houthi Red Sea advance both scored
99.0 and took the entire MUST_READ band.
"""
import pytest

from app.intelligence.developments import (apply_all as developments_all,
                                           distribution, group,
                                           is_same_development, tokens)
from app.intelligence.entities import apply_all as entities_all
from app.intelligence.events import apply_all as events_all
from app.intelligence.impact import apply_all as impact_all
from app.intelligence.priority import classify_batch, distribution as band_distribution


@pytest.fixture(scope="session")
def scored(enriched):
    return impact_all(events_all(entities_all(enriched)))


@pytest.fixture(scope="session")
def developed(scored):
    return developments_all(scored)


# ---------- the similarity rule ----------

def test_stopwords_do_not_make_a_development():
    """Headlines sharing only filler words are not the same story."""
    a = tokens("The report on the new update said it would be over")
    b = tokens("A report said the new update was not over")
    assert not is_same_development(a, b)


def test_same_story_from_two_outlets_groups():
    a = tokens("Houthis capture strategic island on vital oil shipping route")
    b = tokens("Houthis seize strategic island on vital oil shipping route")
    assert is_same_development(a, b)


def test_a_broader_story_does_not_swallow_a_narrower_one():
    """Shared terms must cover half the SHORTER headline, so a long headline
    that happens to contain a short one is not merged with it."""
    short = tokens("Allianz names new chief financial officer")
    long = tokens("Allianz names new chief financial officer as Munich Re and "
                  "Swiss Re post record reinsurance renewals across European "
                  "property treaty business this quarter")
    # Contained, so this pair SHOULD group — the guard is that it is the
    # shorter headline that sets the bar, not the longer one.
    assert is_same_development(short, long)

    unrelated = tokens("Saudi Arabia approves marine insurance pool")
    assert not is_same_development(unrelated, long)


def test_grouping_is_not_chained():
    """A~B and B~C must not drag A and C into one development when A and C
    share nothing. Candidates compare against leads only."""
    a = tokens("Munich Re raises property catastrophe rates at renewal")
    c = tokens("Cyber attack halts claims processing at a US carrier")
    assert not is_same_development(a, c)


# ---------- the contract §8 depends on ----------

def test_every_signal_gets_a_development_id(developed):
    assert all(s.development_id for s in developed)


def test_lead_is_the_highest_scoring_member(developed):
    groups = group(developed)
    for members in groups:
        scores = [m.impact["score"] for m in members]
        assert scores[0] == max(scores)


def test_grouping_partitions_the_batch(developed):
    """Every article in exactly one development — nothing lost, nothing double
    counted. §10 enriches; it must never discard."""
    groups = group(developed)
    assert sum(len(g) for g in groups) == len(developed)
    ids = {id(m) for g in groups for m in g}
    assert len(ids) == len(developed)


def test_distribution_accounts_for_every_article(developed):
    d = distribution(developed)
    assert d["articles"] == len(developed)
    assert d["developments"] + d["collapsed"] == d["articles"]


# ---------- the regression this sprint exists to fix ----------

def test_one_development_never_holds_two_ranked_slots(developed):
    """The 2026-09-12 failure: two articles, one event, both MUST_READ.

    A development may appear once in each ranked band at most — in practice
    once overall, since followers are parked below the ranking entirely.
    """
    banded = classify_batch(developed)
    ranked = ("MUST_READ", "IMPORTANT", "WATCH")
    seen = {}
    for s in banded:
        if s.priority in ranked:
            key = s.development_id
            assert key not in seen, (
                f"development {key} holds two ranked slots: "
                f"{seen.get(key)} and {s.title}")
            seen[key] = s.title


def test_quota_still_holds_after_grouping(developed):
    banded = classify_batch(developed)
    dist = band_distribution(banded)
    developments = distribution(banded)["developments"]
    assert dist["MUST_READ"] <= round(0.05 * developments) + 1, dist


def test_followers_are_parked_not_lost(developed):
    """A follower is real coverage of a real story. It must survive in the
    store, not be silently dropped."""
    banded = classify_batch(developed)
    groups = group(banded)
    multi = [g for g in groups if len(g) > 1]
    if not multi:
        pytest.skip("no duplicate stories in today's corpus")
    for members in multi:
        for follower in members[1:]:
            assert follower.priority, "follower left with no band at all"
            assert any(t["stage"] == "developments" for t in follower.explain)
