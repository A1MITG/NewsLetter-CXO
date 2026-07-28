"""Sprint 7 (§7). Executive Impact Score.

Four dimensions, not the PRD's twelve. Each is derived from something an
earlier sprint measured, so a score can be explained rather than asserted:

    materiality  <- event significance (§6), entity richness (§5)
    urgency      <- freshness bucket (§3), urgency of the event type
    credibility  <- source trust weight (§2)
    novelty      <- penalty for routine headline shapes

The composite is 0-100 because it is a sort key. §8 turns it into five bands,
and the bands are what a reader sees — no one is asked to believe that 71
means something different from 68.
"""
import pathlib
import re
from functools import lru_cache

import yaml

from app.intelligence.events import max_significance
from app.intelligence.trust import weight as trust_weight

CONFIG = pathlib.Path(__file__).resolve().parents[2] / "config" / "impact.yaml"


@lru_cache(maxsize=1)
def _config() -> dict:
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8")) or {}


@lru_cache(maxsize=1)
def _routine_rx():
    return [re.compile(p, re.IGNORECASE)
            for p in (_config().get("routine_markers") or [])]


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


def materiality(signal) -> float:
    """Does this move money or risk?"""
    cfg = _config()
    score = max_significance(signal.events) / 5.0

    ent_cfg = cfg.get("material_entities", {})
    for kind, bump in ent_cfg.items():
        if signal.entities.get(kind):
            score += bump

    # A confidently-classified article is more likely to be about something.
    if signal.domains:
        score += 0.10 * signal.domains[0].get("confidence", 0.0)
    return _clamp(score)


def urgency(signal) -> float:
    """Does this need attention now?"""
    cfg = _config()
    score = float(signal.freshness.get("weight", 0.0))
    urgent = set(cfg.get("urgent_events") or [])
    if any(e["type"] in urgent for e in signal.events):
        score += 0.25
    return _clamp(score)


def credibility(signal) -> float:
    """Rescale trust weight (which floors at 0.55) onto a full 0-1 range so it
    can actually discriminate inside this composite."""
    w = trust_weight(signal.source.authority, signal.source.independence)
    return _clamp((w - 0.55) / 0.45)


def novelty(signal) -> float:
    """Is this a development, or this week's regular column?"""
    cfg = _config()
    score = float(cfg.get("base_novelty", 0.85))
    text = signal.title or ""
    if any(rx.search(text) for rx in _routine_rx()):
        score -= float(cfg.get("routine_penalty", 0.45))
    # A detected event is by definition something happening.
    if signal.events:
        score += float(cfg.get("event_novelty_bonus", 0.15))
    return _clamp(score)


def score(signal) -> dict:
    """-> {score: 0-100, dimensions: {...}}"""
    w = _config().get("weights", {})
    dims = {
        "materiality": round(materiality(signal), 3),
        "urgency": round(urgency(signal), 3),
        "credibility": round(credibility(signal), 3),
        "novelty": round(novelty(signal), 3),
    }
    composite = sum(dims[k] * float(w.get(k, 0.0)) for k in dims)
    return {"score": round(100 * _clamp(composite), 1), "dimensions": dims}


def apply(signal):
    """Populate signal.impact in place, with a trace (§11)."""
    result = score(signal)
    signal.impact = result
    top = max(result["dimensions"], key=result["dimensions"].get)
    signal.trace("impact",
                 f"score {result['score']} (strongest dimension: {top})",
                 result["dimensions"])
    return signal


def apply_all(signals: list) -> list:
    for s in signals:
        apply(s)
    return signals
