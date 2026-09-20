"""Build the canonical intelligence store.

One scrape, one scoring pass, one published artifact. The Command Center and
the Signals newsletter are both projections of this file, so the two surfaces
cannot drift apart — which is how signals.json and command_center_data.json
came to be a day out of sync under the old two-script build.

Nothing here calls a model. Sections 1-8 and 11 are entirely deterministic.

Usage:
    python scripts/build_intelligence_store.py                 # use cache
    python scripts/build_intelligence_store.py --refresh       # re-scrape
    python scripts/build_intelligence_store.py --out PATH
"""
import argparse
import json
import pathlib
import sys
from collections import Counter
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.intelligence.developments import apply_all as developments_all  # noqa: E402
from app.intelligence.developments import distribution as dev_distribution  # noqa: E402
from app.intelligence.domains import apply_all as domains_all          # noqa: E402
from app.intelligence.entities import apply_all as entities_all        # noqa: E402
from app.intelligence.events import apply_all as events_all            # noqa: E402
from app.intelligence.freshness import apply_all as freshness_all      # noqa: E402
from app.intelligence.impact import apply_all as impact_all            # noqa: E402
from app.intelligence.normalize import normalize_all                   # noqa: E402
from app.intelligence.priority import BANDS, classify_batch, distribution  # noqa: E402
from app.intelligence.trust import apply_all as trust_all              # noqa: E402

DEFAULT_OUT = ROOT / "docs" / "design_previews" / "2026-07-28-live" / "intelligence_store.json"


def build(refresh: bool = False) -> dict:
    if refresh:
        from dotenv import load_dotenv
        load_dotenv()
        from app.scraper.store import get_articles
        raw = get_articles(force_refresh=True)
        data_date = datetime.now(timezone.utc).date().isoformat()
    else:
        cache = json.loads(
            (ROOT / "instance" / "articles_cache.json").read_text(encoding="utf-8"))
        raw = cache["articles"]
        data_date = cache.get("date", "unknown")

    # The pipeline, in order. Each stage enriches; none discards.
    signals = normalize_all(raw)
    signals = trust_all(signals)
    signals = freshness_all(signals)
    signals = domains_all(signals)
    signals = entities_all(signals)
    signals = events_all(signals)
    signals = impact_all(signals)
    # §10 runs between impact and priority: it needs scores to pick a lead,
    # and priority needs the grouping to stop one story taking two slots.
    signals = developments_all(signals)
    signals = classify_batch(signals)

    engines = {}
    for s in signals:
        if s.priority == "IGNORE" or not s.engine_id:
            continue
        e = engines.setdefault(s.engine_id, {
            "engine": s.engine_id,
            "display": s.domains[0]["display"],
            "signal": s.domains[0]["signal"],
            "count": 0,
        })
        e["count"] += 1

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        # The date of the DATA, not of the build. These differ, and conflating
        # them is what let April-2024 articles be labelled "today".
        "data_date": data_date,
        "counts": {
            "scraped": len(raw),
            "signals": len(signals),
            "current": sum(1 for s in signals if s.freshness.get("is_current")),
            "classified": sum(1 for s in signals if s.domains),
            "developments": dev_distribution(signals),
            "by_priority": distribution(signals),
            "by_tier": dict(Counter(s.source.tier for s in signals)),
        },
        "engines": sorted(engines.values(), key=lambda e: -e["count"]),
        "bands": list(BANDS),
        "signals": [s.to_dict() for s in signals if s.priority != "IGNORE"],
    }


def main(refresh: bool, out: str) -> int:
    store = build(refresh)
    path = pathlib.Path(out) if out else DEFAULT_OUT
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(store, ensure_ascii=False, indent=1), encoding="utf-8")

    c = store["counts"]
    print(f"data date   : {store['data_date']}")
    print(f"scraped     : {c['scraped']}")
    print(f"signals     : {c['signals']}  ({c['current']} current, "
          f"{c['classified']} classified)")
    d = c["developments"]
    print(f"developments: {d['developments']} distinct  "
          f"({d['collapsed']} duplicate articles collapsed, "
          f"largest group {d['largest']})")
    print("priority    : " + "  ".join(f"{k}={v}" for k, v in c["by_priority"].items()))
    print(f"published   : {len(store['signals'])} (IGNORE excluded)")
    shown = path.resolve()
    try:
        shown = shown.relative_to(ROOT)
    except ValueError:
        pass          # --out pointed outside the repo; show it absolute
    print(f"wrote       : {shown}  "
          f"({path.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--refresh", action="store_true", help="re-scrape before building")
    p.add_argument("--out", default="", help="output path")
    raise SystemExit(main(**vars(p.parse_args())))
