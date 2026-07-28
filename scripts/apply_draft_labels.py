"""Apply DRAFT priority labels to data/gold_set.jsonl, and emit a review CSV.

These labels are a first pass, not ground truth. They are tagged
`labelled_by: draft` so every measurement taken against them can be reported
as provisional, and so a human pass can be detected (labelled_by: human).

Why a draft at all: labelling 150 rows from scratch is ~45 minutes; reviewing
150 pre-labelled rows is ~10. The reviewer's overrides are what make the bar
theirs — this only changes the starting point.

Rubric applied (audience: insurance CEO / GCC head / CXO):
  MUST_READ  changes a decision this week
  IMPORTANT  changes how you'd think; wanted in the brief
  WATCH      developing thread worth tracking, no action yet
  BACKGROUND real context, wouldn't change a decision
  IGNORE     noise, sport, crime, celebrity, listings, off-domain

Usage:
    python scripts/apply_draft_labels.py          # write labels + review.csv
    python scripts/apply_draft_labels.py --stats  # distribution only
"""
import argparse
import csv
import json
import pathlib
import sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[1]
GOLD = ROOT / "data" / "gold_set.jsonl"
REVIEW = ROOT / "data" / "gold_set_review.csv"

MUST_READ = {63, 72, 74, 75, 80, 81, 91, 128, 143}

IMPORTANT = {1, 6, 10, 12, 16, 23, 32, 33, 39, 43, 47, 58, 69, 71, 73, 76,
             84, 87, 89, 93, 96, 109, 113, 115, 125, 126, 130, 133, 144, 148}

WATCH = {0, 4, 7, 14, 18, 21, 24, 29, 36, 40, 45, 46, 59, 60, 64, 67, 68, 77,
         83, 99, 101, 103, 105, 106, 107, 108, 110, 111, 112, 117, 119, 120,
         124, 129, 136, 139, 142}

IGNORE = {5, 8, 15, 22, 25, 48, 49, 50, 55, 65, 70, 79, 85, 90, 95, 97, 114,
          118, 132, 134, 145, 146}

# Everything not listed above is BACKGROUND.


def label_for(index: int) -> str:
    if index in MUST_READ:
        return "MUST_READ"
    if index in IMPORTANT:
        return "IMPORTANT"
    if index in WATCH:
        return "WATCH"
    if index in IGNORE:
        return "IGNORE"
    return "BACKGROUND"


def main(stats_only: bool) -> int:
    rows = [json.loads(l) for l in GOLD.read_text(encoding="utf-8").splitlines()
            if l.strip()]

    overlap = (MUST_READ & IMPORTANT) | (MUST_READ & WATCH) | (IMPORTANT & WATCH) \
              | (WATCH & IGNORE) | (MUST_READ & IGNORE) | (IMPORTANT & IGNORE)
    if overlap:
        print(f"ERROR: indices in more than one bucket: {sorted(overlap)}", file=sys.stderr)
        return 1

    for i, row in enumerate(rows):
        # Never overwrite a human decision.
        if row.get("labelled_by") == "human" and row.get("priority"):
            continue
        row["priority"] = label_for(i)
        row["labelled_by"] = "draft"

    dist = Counter(r["priority"] for r in rows)
    order = ["MUST_READ", "IMPORTANT", "WATCH", "BACKGROUND", "IGNORE"]
    print("DRAFT LABEL DISTRIBUTION")
    for k in order:
        n = dist.get(k, 0)
        print("  %-11s %3d  %4.0f%%  %s" % (k, n, 100 * n / len(rows), "#" * (n // 2)))

    if stats_only:
        return 0

    with GOLD.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    with REVIEW.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["index", "draft_priority", "your_priority", "source", "title", "url"])
        for i, row in enumerate(rows):
            host = row["url"].split("/")[2].replace("www.", "") if "//" in row["url"] else ""
            w.writerow([i, row["priority"], "", host, row["title"], row["url"]])

    print(f"\nWrote labels to {GOLD.relative_to(ROOT)}")
    print(f"Wrote review sheet to {REVIEW.relative_to(ROOT)}")
    print("Fill 'your_priority' only where you disagree, then run "
          "scripts/merge_review.py")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--stats", action="store_true", help="print distribution only")
    raise SystemExit(main(p.parse_args().stats))
