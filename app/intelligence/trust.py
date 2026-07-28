"""Sprint 2 (§2). Source Trust Framework.

Resolves a hostname to a tier plus two orthogonal scores, and turns those
into a ranking weight. The PRD is explicit that trust must influence
ranking but never suppress important information outright — so weight() is
floored well above zero. A Reuters scoop and the same story from an unknown
blog differ in rank, not in whether they exist.
"""
import pathlib
from functools import lru_cache

import yaml

CONFIG = pathlib.Path(__file__).resolve().parents[2] / "config" / "sources.yaml"

# Trust never zeroes a story out — it re-ranks. An unknown source keeps at
# least this share of its intrinsic score.
WEIGHT_FLOOR = 0.55


@lru_cache(maxsize=1)
def _config() -> dict:
    if not CONFIG.exists():
        return {"defaults": {"tier": "unknown", "authority": 0.35, "independence": 0.50},
                "tiers": {}, "sources": {}}
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8")) or {}


def resolve(host: str) -> dict:
    """Hostname -> {tier, authority, independence}.

    Exact match first, then parent domain (so ``feeds.bbci.co.uk`` inherits
    ``bbci.co.uk``), then defaults. Never raises: an unrecognised source is
    a valid, lower-weighted state, not an error.
    """
    cfg = _config()
    defaults = cfg.get("defaults", {})
    tiers = cfg.get("tiers", {})
    sources = cfg.get("sources", {})

    host = (host or "").lower().replace("www.", "")
    entry = None
    if host in sources:
        entry = sources[host]
    else:
        parts = host.split(".")
        for i in range(1, max(1, len(parts) - 1)):
            parent = ".".join(parts[i:])
            if parent in sources:
                entry = sources[parent]
                break

    entry = entry or {}
    tier = entry.get("tier", defaults.get("tier", "unknown"))
    tier_defaults = tiers.get(tier, {})

    return {
        "tier": tier,
        "authority": float(entry.get("authority",
                     tier_defaults.get("authority", defaults.get("authority", 0.35)))),
        "independence": float(entry.get("independence",
                       tier_defaults.get("independence", defaults.get("independence", 0.50)))),
        "known": bool(entry),
    }


def weight(authority: float, independence: float) -> float:
    """Combine into a single ranking multiplier in [WEIGHT_FLOOR, 1.0].

    Authority is weighted more heavily than independence: for executive
    intelligence, domain expertise on the story matters more than arms-length
    distance from it. A trade journal reporting its own beat should outrank a
    general-interest outlet covering the same story in passing.
    """
    raw = 0.65 * authority + 0.35 * independence
    return round(WEIGHT_FLOOR + (1.0 - WEIGHT_FLOOR) * max(0.0, min(1.0, raw)), 4)


def apply(signal) -> "Signal":
    """Populate a Signal's Source trust fields in place, with a trace (§11)."""
    info = resolve(signal.source.domain)
    signal.source.tier = info["tier"]
    signal.source.authority = info["authority"]
    signal.source.independence = info["independence"]
    w = weight(info["authority"], info["independence"])
    signal.trace(
        "trust",
        f"{signal.source.domain or '?'} -> {info['tier']} (weight {w})",
        {"authority": info["authority"], "independence": info["independence"],
         "weight": w, "configured": info["known"]},
    )
    return signal


def apply_all(signals: list) -> list:
    for s in signals:
        apply(s)
    return signals
