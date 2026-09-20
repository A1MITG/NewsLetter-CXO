"""Sprint 10 (§10). Developments.

Two outlets reporting the same event are two articles and one development.
Every stage before this one scores an article in isolation, so none of them
can know that — §8 then ranks inside a quota, where duplicates do real harm.
On the 2026-09-12 build both MUST_READ slots went to the same Houthi Red Sea
advance, scoring 99.0 twice.

The legacy Signals page never had this problem: synthesize_signals() drops
near-duplicate headlines while filling a bucket. This module is that rule,
moved into the pipeline and lifted into config/developments.yaml so it is
visible and reversible rather than buried.

Ordering matters. This runs AFTER §7 impact, because the highest-scoring
member of a group becomes its lead, and BEFORE §8 priority, which is the
stage that acts on the grouping.

This stage never discards. Every signal keeps its place and gains a
development_id; singletons get one too, so "which development is this?" is
always answerable. What a follower is worth is §8's decision, not this one's.
"""
import hashlib
import pathlib
import re
from functools import lru_cache

import yaml

CONFIG = pathlib.Path(__file__).resolve().parents[2] / "config" / "developments.yaml"


@lru_cache(maxsize=1)
def _config() -> dict:
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8")) or {}


@lru_cache(maxsize=1)
def _stopwords() -> frozenset:
    return frozenset(_config().get("stopwords") or [])


def _normalize(text: str) -> str:
    """Lowercase and straighten curly quotes, so terms compare consistently."""
    return (text or "").lower().replace("’", "'").replace("‘", "'")


def tokens(title: str) -> frozenset:
    """Meaningful-word set of a headline, for near-duplicate comparison."""
    min_len = int(_config().get("similarity", {}).get("min_term_length", 1))
    words = re.findall(r"[a-z0-9']+", _normalize(title))
    words = [w[:-2] if w.endswith("'s") else w.rstrip("'") for w in words]
    stop = _stopwords()
    return frozenset(w for w in words if w not in stop and len(w) > min_len)


def is_same_development(a: frozenset, b: frozenset) -> bool:
    """Same story retold.

    Both conditions have to hold: enough shared terms that it is not
    coincidence, and enough coverage of the shorter headline that one story
    is not merely contained in a broader one.
    """
    cfg = _config().get("similarity", {})
    shared = len(a & b)
    if shared < int(cfg.get("min_shared_terms", 3)):
        return False
    shorter = max(1, min(len(a), len(b)))
    return shared / shorter >= float(cfg.get("min_overlap", 0.5))


def _development_id(lead_tokens: frozenset) -> str:
    """Stable across builds: the same story yields the same id tomorrow."""
    key = " ".join(sorted(lead_tokens))
    return "dev-" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:10]


def group(signals: list) -> list:
    """-> [[lead, follower, ...], ...], strongest member first in each group.

    Greedy, in descending impact order, comparing each candidate against the
    LEADS only. Comparing against every member would let A~B and B~C chain A
    to C even where A and C share nothing.
    """
    ordered = sorted(signals,
                     key=lambda s: s.impact.get("score", 0.0), reverse=True)
    groups: list[list] = []
    lead_tokens: list[frozenset] = []

    for s in ordered:
        t = tokens(s.title)
        for i, lt in enumerate(lead_tokens):
            if is_same_development(t, lt):
                groups[i].append(s)
                break
        else:
            groups.append([s])
            lead_tokens.append(t)
    return groups


def apply_all(signals: list) -> list:
    """Populate signal.development_id in place, with traces (§11)."""
    for members in group(signals):
        lead = members[0]
        did = _development_id(tokens(lead.title))
        for s in members:
            s.development_id = did
        if len(members) == 1:
            lead.trace("developments", f"{did}: single article", None)
            continue

        lead.trace(
            "developments",
            f"{did}: lead of {len(members)} articles on one development",
            {"id": did, "size": len(members), "role": "lead",
             "others": [m.title for m in members[1:]]})
        for s in members[1:]:
            s.trace(
                "developments",
                f"{did}: same development as \"{lead.title}\"",
                {"id": did, "size": len(members), "role": "follower",
                 "lead": lead.title, "lead_score": lead.impact.get("score")})
    return signals


def distribution(signals: list) -> dict:
    """-> {developments, articles, largest, collapsed} for the build summary."""
    sizes: dict[str, int] = {}
    for s in signals:
        if s.development_id:
            sizes[s.development_id] = sizes.get(s.development_id, 0) + 1
    return {
        "developments": len(sizes),
        "articles": len(signals),
        "largest": max(sizes.values(), default=0),
        "collapsed": sum(n - 1 for n in sizes.values()),
    }
