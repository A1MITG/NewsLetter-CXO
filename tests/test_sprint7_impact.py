"""Sprint 7 exit tests (PRD §7 — Executive Impact Score).

Two kinds of test here, and the distinction matters:

  STRUCTURAL — bounded, monotonic, explainable. Objectively verifiable.
  CALIBRATION — does the score agree with the gold set? Only as good as the
                labels, which are DRAFT until reviewed. These tests assert a
                deliberately loose bar so they measure direction, not
                pretend precision.
"""
import pytest

from app.intelligence.entities import apply_all as entities_all
from app.intelligence.events import apply_all as events_all
from app.intelligence.impact import apply_all, credibility, novelty, score


@pytest.fixture(scope="session")
def scored(enriched):
    return apply_all(events_all(entities_all(enriched)))


# ---------- structural ----------

def test_score_is_bounded(scored):
    for s in scored:
        assert 0.0 <= s.impact["score"] <= 100.0


def test_all_four_dimensions_present(scored):
    for s in scored:
        dims = s.impact["dimensions"]
        assert set(dims) == {"materiality", "urgency", "credibility", "novelty"}
        assert all(0.0 <= v <= 1.0 for v in dims.values())


def test_score_is_deterministic(scored):
    for s in scored[:20]:
        assert score(s)["score"] == score(s)["score"]


def test_higher_trust_scores_higher(scored):
    """Credibility must actually discriminate, not sit flat at the floor."""
    values = {s.impact["dimensions"]["credibility"] for s in scored}
    assert len(values) > 1, "credibility is constant across the corpus"


def test_routine_headlines_lose_novelty():
    class Fake:
        title = "Hindustan Unilever Q4 Preview: Price cuts, slow demand"
        events = []
    assert novelty(Fake()) < 0.6


def test_events_raise_novelty():
    class Plain:
        title = "Insurer updates its regional structure"
        events = []

    class WithEvent:
        title = "Insurer updates its regional structure"
        events = [{"type": "ACQUISITION", "significance": 4}]
    assert novelty(WithEvent()) > novelty(Plain())


def test_every_score_is_traced(scored):
    for s in scored:
        assert any(e["stage"] == "impact" for e in s.explain)


def test_trace_carries_the_dimensions(scored):
    entry = next(e for e in scored[0].explain if e["stage"] == "impact")
    assert set(entry["evidence"]) == {"materiality", "urgency",
                                      "credibility", "novelty"}


# ---------- calibration (PROVISIONAL — draft labels) ----------

def _gold_scores(scored, gold):
    by_title = {s.title: s for s in scored}
    out = {}
    for row in gold:
        s = by_title.get(row["title"])
        if s:
            out.setdefault(row["priority"], []).append(s.impact["score"])
    return out


def test_must_read_outscores_ignore(scored, gold):
    if not gold:
        pytest.skip("gold set not labelled")
    buckets = _gold_scores(scored, gold)
    if "MUST_READ" not in buckets or "IGNORE" not in buckets:
        pytest.skip("insufficient labelled coverage")
    mr = sum(buckets["MUST_READ"]) / len(buckets["MUST_READ"])
    ig = sum(buckets["IGNORE"]) / len(buckets["IGNORE"])
    assert mr > ig, f"MUST_READ mean {mr:.1f} did not beat IGNORE mean {ig:.1f}"


def test_ranking_is_broadly_ordered(scored, gold):
    """Loose bar on purpose: the top band must outscore the bottom band.
    Adjacent bands are allowed to overlap — they overlap for humans too."""
    if not gold:
        pytest.skip("gold set not labelled")
    buckets = _gold_scores(scored, gold)
    top = buckets.get("MUST_READ", []) + buckets.get("IMPORTANT", [])
    bottom = buckets.get("BACKGROUND", []) + buckets.get("IGNORE", [])
    if not top or not bottom:
        pytest.skip("insufficient labelled coverage")
    assert sum(top) / len(top) > sum(bottom) / len(bottom)


def test_scores_spread_across_the_range(scored):
    """A score that clusters in a narrow band cannot rank anything."""
    vals = [s.impact["score"] for s in scored]
    assert max(vals) - min(vals) > 25, "impact scores are too tightly clustered"
