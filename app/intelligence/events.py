"""Sprint 6 (§6). Business-event detection.

Detects the things executives actually act on — acquisitions, sanctions,
rate moves, cyber incidents — as distinct from the topic an article belongs
to. An article can be about AI (domain) and be an acquisition (event); those
are different questions and §7 weighs them differently.

Evidence discipline matches §4: a weak pattern alone never fires an event.
That matters more here than for domains, because Sprint 7 uses events to
raise executive significance — a false positive doesn't merely mis-file an
article, it promotes it up the dashboard.

Veto patterns exist because the obvious keyword is frequently a term of art
in this corpus. "War risk" is an insurance product. "Price war" is
competition. Neither is a conflict. "Names ... its CEO" in a lawsuit lists a
defendant; it is not a hire.

A pattern marked `where: title` counts only in the headline. Some phrasings
are the news in a title and background in body text: "Jamieson Named
President" is an appointment, "Nadella, named CEO in 2014, said..." is not.
"""
import pathlib
import re
from functools import lru_cache

import yaml

CONFIG = pathlib.Path(__file__).resolve().parents[2] / "config" / "events.yaml"

TITLE_MULTIPLIER = 2


@lru_cache(maxsize=1)
def _config() -> dict:
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8")) or {}


@lru_cache(maxsize=1)
def _compiled() -> dict:
    """-> {event_type: {significance, patterns:[(rx,weight,where)], vetoes:[rx]}}"""
    out = {}
    for name, spec in (_config().get("events") or {}).items():
        patterns = []
        for p in spec.get("patterns", []):
            where = p.get("where", "any")
            # A typo here would silently widen a title-only pattern to
            # summaries, which is exactly the false positive it exists to stop.
            if where not in ("any", "title"):
                raise ValueError(f"{name}: unknown where={where!r} for {p['rx']}")
            patterns.append((re.compile(p["rx"], re.IGNORECASE), int(p["weight"]), where))
        out[name] = {
            "significance": int(spec.get("significance", 1)),
            "patterns": patterns,
            "vetoes": [re.compile(v, re.IGNORECASE) for v in spec.get("veto", [])],
        }
    return out


def detect(title: str, summary: str = "") -> list:
    """-> [{type, significance, score, confidence, evidence:[...]}] """
    cfg = _config().get("detection", {})
    min_score = int(cfg.get("min_score", 3))
    decisive = int(cfg.get("decisive_weight", 3))

    title = title or ""
    summary = summary or ""
    found = []

    for name, spec in _compiled().items():
        # A veto anywhere kills the event outright.
        vetoed = next((v.pattern for v in spec["vetoes"]
                       if v.search(title) or v.search(summary)), None)
        if vetoed:
            continue

        score, evidence = 0, []
        for rx, weight, where in spec["patterns"]:
            m = rx.search(title)
            if m:
                score += weight * TITLE_MULTIPLIER
                evidence.append({"pattern": rx.pattern, "weight": weight,
                                 "where": "title", "matched": m.group(0)})
                continue
            if summary and where != "title":
                m = rx.search(summary)
                if m:
                    score += weight
                    evidence.append({"pattern": rx.pattern, "weight": weight,
                                     "where": "summary", "matched": m.group(0)})

        if not evidence or score < min_score:
            continue
        # One pattern only counts alone if it is decisive.
        if len(evidence) < 2 and not any(e["weight"] >= decisive for e in evidence):
            continue

        found.append({
            "type": name,
            "significance": spec["significance"],
            "score": score,
            "confidence": round(min(1.0, score / 8.0), 3),
            "evidence": evidence,
        })

    found.sort(key=lambda e: (e["significance"], e["score"]), reverse=True)
    return found


def max_significance(events: list) -> int:
    """What Sprint 7 consumes: the weight of the most significant event."""
    return max((e["significance"] for e in events), default=0)


def apply(signal):
    """Populate signal.events in place, with a trace (§11)."""
    events = detect(signal.title, signal.summary)
    signal.events = events
    if events:
        signal.trace("events",
                     f"detected {len(events)}: "
                     f"{', '.join(e['type'] for e in events)}",
                     [{"type": e["type"], "significance": e["significance"],
                       "matched": [x["matched"] for x in e["evidence"]]}
                      for e in events])
    else:
        signal.trace("events", "no business event cleared the evidence bar", None)
    return signal


def apply_all(signals: list) -> list:
    for s in signals:
        apply(s)
    return signals
