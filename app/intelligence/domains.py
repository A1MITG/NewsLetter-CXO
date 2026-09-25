"""Sprint 4 (§4). Multi-dimensional domain detection.

Three changes from the legacy classifier in app/analysis/signals.py:

1. An article may hold several domains, with a primary and secondaries.
   The old winner-takes-all meant an insurer's AI story appeared once, and
   an article whose best score was Executive was deleted entirely because
   the Command Center had no Executive tile.

2. Evidence rules replace a bare threshold. One weight-2 keyword no longer
   classifies anything: 39% of live classifications rested on a single
   keyword, which is how a person surnamed "Stock" became a markets story.

3. Every assignment carries its evidence — which keywords fired, at what
   weight, in title or summary. §11 is built in, not bolted on.

Keywords are imported from the legacy module rather than duplicated. Those
weights encode real bug fixes (the Air India and Wipro cases) and should
have exactly one home.
"""
import pathlib
import re
from functools import lru_cache

import yaml

from app.analysis.gcc_rubric import GCC_TERM, gcc_axes, gcc_means_gulf
from app.analysis.signals import KEYWORDS, _normalize

CONFIG = pathlib.Path(__file__).resolve().parents[2] / "config" / "domains.yaml"

TITLE_MULTIPLIER = 2

# Legacy signal name -> our domain key.
_SIGNAL_TO_DOMAIN = {
    "Signal Global": "global",
    "Signal Business": "economy",
    "Signal AI": "ai",
    "Signal GCC": "gcc",
    "Signal Insurance": "insurance",
    "Signal Executive": "executive",
}


@lru_cache(maxsize=1)
def _config() -> dict:
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _compiled() -> dict:
    """Legacy keyword tables, plus the supplementary terms in domains.yaml.

    The legacy tables stay authoritative and unedited — they are shared with
    the live Signals page. Gaps found by this pipeline are filled in config,
    where they are visible and reversible.
    """
    out = {}
    for signal_name, kws in KEYWORDS.items():
        domain = _SIGNAL_TO_DOMAIN.get(signal_name)
        if not domain:
            continue
        out[domain] = [(kw, re.compile(r"\b" + re.escape(kw) + r"\b"), w)
                       for kw, w in kws.items()]

    for domain, extra in (_config().get("supplementary") or {}).items():
        if domain not in out:
            continue
        known = {kw for kw, _, _ in out[domain]}
        for kw, w in extra.items():
            if kw not in known:
                out[domain].append(
                    (kw, re.compile(r"\b" + re.escape(kw) + r"\b"), int(w)))
    return out


def score_domains(title: str, summary: str = "") -> dict:
    """-> {domain: {"score": int, "evidence": [...]}} for every domain."""
    t, s = _normalize(title or ""), _normalize(summary or "")
    results = {}

    for domain, patterns in _compiled().items():
        score, evidence = 0, []
        for kw, rx, w in patterns:
            if rx.search(t):
                score += w * TITLE_MULTIPLIER
                evidence.append({"keyword": kw, "weight": w, "where": "title"})
            elif s and rx.search(s):
                score += w
                evidence.append({"keyword": kw, "weight": w, "where": "summary"})
        results[domain] = {"score": score, "evidence": evidence}

    # "GCC" meaning the Gulf Cooperation Council, by the same rule the
    # legacy classifier applies (gcc_rubric.gcc_means_gulf).
    if gcc_means_gulf(f"{t} {s}"):
        in_title = bool(GCC_TERM.search(t))
        if in_title or (s and GCC_TERM.search(s)):
            mult = TITLE_MULTIPLIER if in_title else 1
            gcc_weight = KEYWORDS["Signal GCC"]["gcc"]
            results["gcc"]["score"] = max(0, results["gcc"]["score"] - gcc_weight * mult)
            results["global"]["score"] += 2 * mult
            results["gcc"]["evidence"].append(
                {"keyword": "gcc", "weight": 0, "where": "vetoed: Gulf context"})

    # Same two-axis gate the legacy classifier applies, from the same
    # definition. Evidence rules count keywords; they cannot ask what KIND of
    # thing each keyword is, which is why "noida + gurugram" cleared
    # min_score 6 and min_distinct_keywords 2 while naming no capability
    # centre and no action taken on one.
    if results.get("gcc", {}).get("score"):
        has_entity, has_action = gcc_axes(title, summary)
        if not (has_entity and has_action):
            results["gcc"]["score"] = 0
            results["gcc"]["evidence"].append(
                {"keyword": "", "weight": 0,
                 "where": "gated: needs an entity and an action"})
    return results


def _qualifies(entry: dict, cfg: dict) -> bool:
    """Evidence rule — the fix for single-keyword classification."""
    ev = [e for e in entry["evidence"] if e["weight"] > 0]
    if entry["score"] < cfg["min_score"]:
        return False
    if len(ev) >= cfg["min_distinct_keywords"]:
        return True
    # A single keyword suffices only if it is decisive on its own.
    return any(e["weight"] >= cfg["decisive_weight"] for e in ev)


def classify(title: str, summary: str = "") -> dict:
    """-> {"primary": str|None, "secondary": [...], "domains": [...]}"""
    cfg = _config()
    ev_cfg = cfg["evidence"]
    divisor = float(cfg["confidence_divisor"])

    scored = score_domains(title, summary)
    qualified = [(d, e) for d, e in scored.items() if _qualifies(e, ev_cfg)]
    qualified.sort(key=lambda kv: kv[1]["score"], reverse=True)

    if not qualified:
        return {"primary": None, "secondary": [], "domains": []}

    top_domain, top_entry = qualified[0]
    cutoff = top_entry["score"] * float(cfg["secondary_ratio"])

    domains = []
    for rank, (d, e) in enumerate(qualified):
        if rank > 0 and e["score"] < cutoff:
            continue
        meta = cfg["domains"][d]
        domains.append({
            "domain": d,
            "role": "primary" if rank == 0 else "secondary",
            "score": e["score"],
            "confidence": round(min(1.0, e["score"] / divisor), 3),
            "evidence": [x for x in e["evidence"] if x["weight"] > 0],
            "engine": meta["engine"],
            "signal": meta["signal"],
            "display": meta["display"],
        })

    return {"primary": top_domain,
            "secondary": [d["domain"] for d in domains[1:]],
            "domains": domains}


def apply(signal):
    """Populate signal.domains / engine_id / signal_name, with a trace."""
    result = classify(signal.title, signal.summary)
    signal.domains = result["domains"]
    if result["primary"]:
        primary = result["domains"][0]
        signal.engine_id = primary["engine"]
        signal.signal_name = primary["signal"]
        signal.trace("domains",
                     f"primary={result['primary']} "
                     f"(score {primary['score']}, {len(primary['evidence'])} keywords)",
                     {"secondary": result["secondary"],
                      "evidence": primary["evidence"]})
    else:
        signal.trace("domains", "no domain cleared the evidence bar",
                     {"best": max((e["score"] for e in
                                   score_domains(signal.title, signal.summary).values()),
                                  default=0)})
    return signal


def apply_all(signals: list) -> list:
    for s in signals:
        apply(s)
    return signals


def classified_only(signals: list) -> list:
    return [s for s in signals if s.domains]
