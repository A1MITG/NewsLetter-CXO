"""Merge a reviewed CSV back into data/gold_set.jsonl.

Only rows where `your_priority` is filled in are changed, and those rows are
re-tagged `labelled_by: human` so subsequent measurements can report how much
of the bar is actually yours.

Usage:
    python scripts/merge_review.py
"""
import csv
import json
import pathlib
import sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[1]
GOLD = ROOT / "data" / "gold_set.jsonl"
REVIEW = ROOT / "data" / "gold_set_review.csv"
VALID = {"MUST_READ", "IMPORTANT", "WATCH", "BACKGROUND", "IGNORE"}


def main() -> int:
    if not REVIEW.exists():
        print(f"No {REVIEW.relative_to(ROOT)} — run apply_draft_labels.py first",
              file=sys.stderr)
        return 1

    rows = [json.loads(l) for l in GOLD.read_text(encoding="utf-8").splitlines()
            if l.strip()]

    changed, invalid = 0, []
    with REVIEW.open(encoding="utf-8", newline="") as f:
        for rec in csv.DictReader(f):
            value = (rec.get("your_priority") or "").strip().upper()
            if not value:
                continue
            if value not in VALID:
                invalid.append((rec.get("index"), value))
                continue
            idx = int(rec["index"])
            if rows[idx]["priority"] != value:
                changed += 1
            rows[idx]["priority"] = value
            rows[idx]["labelled_by"] = "human"

    if invalid:
        print("Invalid labels (ignored):", invalid, file=sys.stderr)

    with GOLD.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    human = sum(1 for r in rows if r.get("labelled_by") == "human")
    print(f"Overrides applied : {changed}")
    print(f"Human-labelled    : {human}/{len(rows)} ({100*human/len(rows):.0f}%)")
    print()
    for k, n in Counter(r["priority"] for r in rows).most_common():
        print("  %-11s %3d" % (k, n))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
