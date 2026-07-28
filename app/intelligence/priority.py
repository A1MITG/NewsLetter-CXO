"""Sprint 8 (§8). Executive importance classification.

Turns the §7 impact score into five bands. Unlike every earlier stage, this
one is inherently relative: "must read" is a claim about an article's place
in today's set, not a property of the article. So classification operates on
the whole batch.

Bands are assigned by rank, bounded by absolute floors:

    quota  stops a dramatic news day flooding the top band
    floor  stops a quiet news day promoting filler into it

Neither works alone. Quotas alone make the best of a slow Tuesday a
must-read; floors alone put thirty wildfire stories above the line.
"""
import pathlib
from functools import lru_cache

import yaml

CONFIG = pathlib.Path(__file__).resolve().parents[2] / "config" / "priority.yaml"

BANDS = ("MUST_READ", "IMPORTANT", "WATCH", "BACKGROUND", "IGNORE")


@lru_cache(maxsize=1)
def _config() -> dict:
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8")) or {}


def _hard_ignore_reason(signal) -> str | None:
    rules = _config().get("hard_ignore", {})
    if rules.get("not_current") and not signal.freshness.get("is_current", False):
        return f"not current ({signal.freshness.get('bucket', '?')})"
    if rules.get("no_domain") and not signal.domains:
        return "no domain cleared the evidence bar"
    return None


def classify_batch(signals: list) -> list:
    """Assign signal.priority across the whole batch, with traces (§11)."""
    cfg = _config()
    bands = cfg.get("bands", [])
    ignore_below = float(cfg.get("ignore_below", 0))

    eligible = []
    for s in signals:
        reason = _hard_ignore_reason(s)
        if reason:
            s.priority = "IGNORE"
            s.trace("priority", f"IGNORE: {reason}", None)
        else:
            eligible.append(s)

    eligible.sort(key=lambda s: s.impact.get("score", 0.0), reverse=True)
    total = len(eligible)

    assigned = 0
    for band in bands:
        name = band["name"]
        cap = int(round(float(band["max_share"]) * total))
        floor = float(band["min_score"])
        placed = 0
        while assigned < total and placed < max(0, cap - assigned):
            s = eligible[assigned]
            score = s.impact.get("score", 0.0)
            if score < ignore_below:
                break                      # everything below is IGNORE
            if score < floor:
                break                      # too weak for this band; try the next
            s.priority = name
            s.trace("priority",
                    f"{name}: rank {assigned + 1}/{total}, score {score}",
                    {"rank": assigned + 1, "of": total, "score": score,
                     "band_floor": floor, "band_cap": cap})
            assigned += 1
            placed += 1

    # Whatever is left is below every floor, or below ignore_below.
    for s in eligible[assigned:]:
        s.priority = "IGNORE"
        s.trace("priority",
                f"IGNORE: score {s.impact.get('score', 0.0)} below all band floors",
                {"score": s.impact.get("score", 0.0)})

    return signals


def distribution(signals: list) -> dict:
    out = {b: 0 for b in BANDS}
    for s in signals:
        if s.priority in out:
            out[s.priority] += 1
    return out


def top(signals: list, bands=("MUST_READ", "IMPORTANT")) -> list:
    chosen = [s for s in signals if s.priority in bands]
    chosen.sort(key=lambda s: s.impact.get("score", 0.0), reverse=True)
    return chosen
