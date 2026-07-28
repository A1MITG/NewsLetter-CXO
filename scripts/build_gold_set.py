"""Sprint 0. Emit a stratified sample of REAL headlines for hand-labelling.

This is the only step in the whole build that requires a human. Everything
downstream (domain detection, impact scoring, priority classification) is
measured against these labels, so nothing after Sprint 4 can be tuned
without them.

Usage:
    python scripts/build_gold_set.py --n 150
    # then open data/gold_set.jsonl and fill in each "priority"
"""
import argparse
import json
import pathlib
import random
import sys
from urllib.parse import urlparse

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PRIORITIES = ["MUST_READ", "IMPORTANT", "WATCH", "BACKGROUND", "IGNORE"]


def _eligible(articles):
    """Same pre-filter the pipeline uses: real articles, no duplicates."""
    seen, pool = set(), []
    for a in articles:
        title = (a.get("title") or "").strip()
        if not title or len(title.split()) < 4:
            continue
        key = title.lower()
        if key in seen:
            continue
        seen.add(key)
        pool.append(a)
    return pool


def _stratify(pool, n):
    """Round-robin across sources so one chatty feed can't dominate."""
    by_source = {}
    for a in pool:
        host = (urlparse(a.get("url", "")).hostname or "?").replace("www.", "")
        by_source.setdefault(host, []).append(a)

    picked, depth = [], 0
    while len(picked) < min(n, len(pool)):
        progressed = False
        for source in sorted(by_source):
            bucket = by_source[source]
            if depth < len(bucket):
                picked.append(bucket[depth])
                progressed = True
                if len(picked) >= n:
                    break
        if not progressed:
            break
        depth += 1
    return picked


def main(n: int, seed: int) -> int:
    cache_path = ROOT / "instance" / "articles_cache.json"
    if not cache_path.exists():
        print("No instance/articles_cache.json — run the scraper first.", file=sys.stderr)
        return 1

    cache = json.loads(cache_path.read_text(encoding="utf-8"))
    pool = _eligible(cache["articles"])
    picked = _stratify(pool, n)
    random.Random(seed).shuffle(picked)

    out = ROOT / "data" / "gold_set.jsonl"
    out.parent.mkdir(exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for a in picked:
            f.write(json.dumps({
                "title": a["title"],
                "url": a.get("url", ""),
                "priority": "",        # <- FILL THIS IN
                "domains": [],         # <- optional
                "_allowed": PRIORITIES,
            }, ensure_ascii=False) + "\n")

    print(f"Wrote {len(picked)} rows to {out.relative_to(ROOT)}")
    print(f"  eligible pool: {len(pool)} of {len(cache['articles'])} scraped")
    print(f"  sources represented: "
          f"{len({(urlparse(a.get('url','')).hostname or '') for a in picked})}")
    print()
    print("Next: label the 'priority' field on each row using one of:")
    print("  " + " / ".join(PRIORITIES))
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--n", type=int, default=150, help="rows to sample")
    p.add_argument("--seed", type=int, default=7, help="shuffle seed")
    raise SystemExit(main(**vars(p.parse_args())))
