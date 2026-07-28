"""Generate the labelling guide: what belongs in which band, per domain.

Two outputs:
  docs/labelling_guide.csv     the 6 x 5 matrix — criteria, decision test,
                               and the mistake most likely to be made
  docs/labelling_examples.csv  real headlines from the current corpus, with
                               their domain, draft band and the evidence the
                               pipeline actually used

The matrix is judgement and lives here in code so it can be argued with and
edited. The examples are pulled live, so they are never invented.

Usage:
    python scripts/build_labelling_guide.py
"""
import csv
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

BANDS = ["MUST_READ", "IMPORTANT", "WATCH", "BACKGROUND", "IGNORE"]

# The one question that governs every call, regardless of domain.
UNIVERSAL = {
    "MUST_READ":  "Changes a decision THIS WEEK. Material, credible, and it would be negligent not to know.",
    "IMPORTANT":  "Changes how you think. You would want it in the brief, but no action is due today.",
    "WATCH":      "A live thread worth tracking. Nothing to do yet, but it could become something.",
    "BACKGROUND": "True and relevant, but inert. It informs context, it does not move anything.",
    "IGNORE":     "You would skip it. Noise, off-domain, or a routine column rather than a development.",
}

GUIDE = {
    "global": {
        "display": "Global Affairs — geopolitics, trade, defence, conflict",
        "MUST_READ": ("Conflict or sanctions that reprice risk NOW: shipping lanes, energy supply, "
                      "war-risk premiums, counterparty exposure.",
                      "Would an underwriter or CFO change a position this week?",
                      "Treating dramatic coverage as material. A vivid war story with no commercial "
                      "channel to your book is BACKGROUND, not MUST_READ."),
        "IMPORTANT": ("Tariffs, trade actions, diplomatic realignment, elections with policy "
                      "consequences in markets you operate in.",
                      "Does it change the operating environment over months?",
                      "Under-rating trade policy because it is not violent."),
        "WATCH": ("Tension building without a commercial channel yet. Regional instability adjacent "
                  "to your exposure.",
                  "Could this become MUST_READ within a quarter?",
                  "Letting WATCH absorb everything you are unsure about."),
        "BACKGROUND": ("International news with no line to your business — humanitarian, domestic "
                       "politics elsewhere, disasters outside your exposure.",
                       "Is it real news that changes nothing for you?",
                       "Confusing 'important to the world' with 'important to this reader'."),
        "IGNORE": ("Crime, celebrity, sport, human-interest colour on an event you already have.",
                   "Would you scroll past it?",
                   "Keeping the third eyewitness account of a fire you already know about."),
    },
    "economy": {
        "display": "Economy, Business & Markets",
        "MUST_READ": ("Central-bank rate decisions, a market shock, a major counterparty in distress, "
                      "M&A that reshapes your competitive set.",
                      "Does it change cost of capital, a counterparty, or the competitive map?",
                      "Promoting big numbers. A large profit at an unrelated company is BACKGROUND."),
        "IMPORTANT": ("Results that signal a sector turn; sizeable M&A or funding in your adjacency; "
                      "macro data that shifts the outlook.",
                      "Would it change a forecast or a plan?",
                      "Treating every earnings release as IMPORTANT."),
        "WATCH": ("Sector trend pieces, mid-size deals, results with a thesis attached.",
                  "Is a pattern forming here?", "Using WATCH for anything with a number in it."),
        "BACKGROUND": ("Routine quarterly results, daily index moves, single-company results outside "
                       "your set.",
                       "Is this just this week's scheduled number?",
                       "None — this is where most business coverage correctly lands."),
        "IGNORE": ("Q4 previews, rich lists, personal finance, listicles.",
                   "Is this a column rather than a development?",
                   "Keeping 'preview' pieces because the company matters."),
    },
    "ai": {
        "display": "AI, Technology & Innovation",
        "MUST_READ": ("A capability, security or regulatory shift that changes build-vs-buy or vendor "
                      "risk this quarter. A major AI security incident.",
                      "Does this change a technology decision already in flight?",
                      "Model-release excitement. A new model is IMPORTANT unless it changes your plan."),
        "IMPORTANT": ("Frontier releases, large AI investment, AI liability or copyright precedent, "
                      "concentration risk in a vendor you depend on.",
                      "Does it change the vendor landscape or the legal exposure?",
                      "Missing legal precedent because it reads as a court story."),
        "WATCH": ("Partnerships, infrastructure buildout, research direction, talent moves.",
                  "Is this the early shape of something?", "Over-collecting vendor press releases."),
        "BACKGROUND": ("Incremental product features, benchmark chatter, funding for small players.",
                       "Interesting but not consequential?", "None."),
        "IGNORE": ("Gadget reviews, consumer app news, AI think-pieces with no specific claim.",
                   "Is there an actual event here?", "Keeping opinion because the topic is hot."),
    },
    "gcc": {
        "display": "GCC & Enterprise Technology — Global Capability Centers, India, shared services",
        "MUST_READ": ("Policy, tax or labour-law change affecting GCC operations, especially with a "
                      "compliance deadline or a penalty precedent.",
                      "Is there a date by which something must change?",
                      "Missing compliance stories because they read as HR news."),
        "IMPORTANT": ("GCC market structure — leasing, headcount trends, state incentives, new "
                      "entrants, wage inflation.",
                      "Does it change the cost or feasibility of the operating model?",
                      "Under-rating real-estate and talent data as 'soft'."),
        "WATCH": ("Individual company GCC expansions, university and talent partnerships, city-level "
                  "incentives.",
                  "Is a location or capability trend forming?", "Collecting every expansion notice."),
        "BACKGROUND": ("Routine India IT-services earnings, generic offshoring commentary.",
                       "Is this the sector's regular news flow?", "None."),
        "IGNORE": ("Generic tech-jobs content, careers advice.",
                   "Is this for a jobseeker rather than an operator?", "None."),
    },
    "insurance": {
        "display": "Insurance & Financial Services",
        "MUST_READ": ("A market pricing turn (rates hardening or softening), a cat event with insured-"
                      "loss implications, a regulatory change touching capital or conduct, or a "
                      "coverage precedent that moves reserves.",
                      "Does this change pricing, capacity, reserves or capital?",
                      "Missing rate-movement stories. 'Property rates down 12%' looks like a "
                      "statistic and is in fact the most actionable line of the day."),
        "IMPORTANT": ("Reinsurer results signalling capacity, mass-tort developments, competitor "
                      "market entry, cat-season forecasts, large verdicts indicating social inflation.",
                      "Does it change the outlook for a line of business?",
                      "Treating large jury awards as legal trivia rather than severity signal."),
        "WATCH": ("Insurtech and product launches, broker leadership moves, rating actions, individual "
                  "carrier results.",
                  "Is this a competitor or capability signal?", "Over-weighting vendor launches."),
        "BACKGROUND": ("Small claims stories, local fraud prosecutions, minor regional results, single "
                       "property losses.",
                       "Is this one claim rather than a pattern?",
                       "Promoting fraud prosecutions because they are insurance-shaped."),
        "IGNORE": ("Book and product listings, 'People:' columns with no material name, tax-fact "
                   "editions.",
                   "Is this a catalogue entry?", "Keeping trade-press filler because the source is trusted."),
    },
    "executive": {
        "display": "Executive & Leadership",
        "MUST_READ": ("A CEO or board change at a major counterparty, competitor or sector bellwether — "
                      "it changes who you deal with, or signals distress.",
                      "Does the identity of the person on the other side of the table change?",
                      "Over-promoting appointments. Most are WATCH."),
        "IMPORTANT": ("Senior leadership change at a named competitor or partner; governance action "
                      "with consequence (fines, board censure, succession disputes).",
                      "Does it signal strategy or trouble?",
                      "Missing governance penalties, which read as compliance minutiae."),
        "WATCH": ("Notable appointments within your sector, especially in lines you compete in.",
                  "Is this someone you will encounter?", "None — most appointments belong here."),
        "BACKGROUND": ("Routine appointment announcements at unrelated firms.",
                       "Would you recognise the company?", "None."),
        "IGNORE": ("'People moves' roundups with no material name, obituaries, awards.",
                   "Is this a column rather than a change?", "None."),
    },
}


def write_matrix(path: pathlib.Path) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["domain", "domain_description", "band", "universal_meaning",
                    "what_qualifies_in_this_domain", "decision_test",
                    "most_likely_mistake"])
        for dom, spec in GUIDE.items():
            for band in BANDS:
                qualifies, test, mistake = spec[band]
                w.writerow([dom, spec["display"], band, UNIVERSAL[band],
                            qualifies, test, mistake])


def write_examples(path: pathlib.Path) -> None:
    store_path = (ROOT / "docs" / "design_previews" / "2026-07-28-live"
                  / "intelligence_store.json")
    if not store_path.exists():
        print("No store yet — run scripts/build_intelligence_store.py first",
              file=sys.stderr)
        return
    store = json.loads(store_path.read_text(encoding="utf-8"))

    rows = []
    for s in store["signals"]:
        dom = s.get("engine_id") or ""
        evidence = ", ".join(e["keyword"] for e in (s["domains"][0]["evidence"]
                                                    if s["domains"] else []))
        rows.append({
            "domain": dom,
            "band": s["priority"],
            "score": s["impact"]["score"],
            "publisher": s["publisher"],
            "title": s["title"],
            "why_this_domain": evidence,
            "events": ", ".join(e["type"] for e in s["events"]),
            "age_hours": (s["freshness"] or {}).get("age_hours"),
            "url": s["canonical_url"],
        })

    order = {b: i for i, b in enumerate(BANDS)}
    rows.sort(key=lambda r: (r["domain"], order.get(r["band"], 9), -r["score"]))

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"  examples: {len(rows)} rows")


def main() -> int:
    docs = ROOT / "docs"
    docs.mkdir(exist_ok=True)
    write_matrix(docs / "labelling_guide.csv")
    print(f"Wrote docs/labelling_guide.csv  ({len(GUIDE) * len(BANDS)} rows)")
    write_examples(docs / "labelling_examples.csv")
    print("Wrote docs/labelling_examples.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
