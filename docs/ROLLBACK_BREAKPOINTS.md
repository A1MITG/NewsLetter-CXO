# SIGNAL — Breakpoints & Rollback Register

A breakpoint (BP) is a commit you can safely return to. This register lists every
one, what it changed, how far it has travelled (local → committed → pushed →
live), and the exact command to roll it back.

*Last updated: 2026-09-24 (BP-23 live) · working branch `final` (GitHub default) · repo `A1MITG/NewsLetter-CXO`
(GitHub now redirects it to `A1MITG/SYGNALZ`).*

---

## Stages

| Stage | Meaning | Rollback risk |
|---|---|---|
| **Local** | Files changed on this machine, not committed | Lost if the folder is deleted; nothing to roll back in git |
| **Committed** | In local git history only | Safe to `reset` — nobody else has it |
| **Pushed** | On `origin/final` | Use `revert`, never `reset` + force-push, unless you mean to rewrite shared history |
| **Live** | Pushed, and its effect is on news-letter-cxo.vercel.app, because it changes what the build publishes to `signals-deploy` | Needs a code rollback **and** a republish of `signals-deploy` |

---

## Breakpoints on `final`

Newest first. BP-01 to BP-04 are inferred from order: only BP-05 and BP-06 carry the
label in their commit message. BP-07 and BP-08 are assigned here.

| BP | Commit | Date (IST) | Stage | Change | What it did | Roll back with |
|---|---|---|---|---|---|---|
| BP-23 | `6626dd1` | 2026-09-24 00:37 | **Live** | ManufacturingTile | The last "coming soon" tile made live, with the same rules as Defence (headline required, floor 5; "plant", "production", "PMI" at 2). Power plants and oil production stay with Energy; film "production", Palantir Foundry, "manufacturing consent" are blanked. Placed after Supply Chain, ahead of AI. Holds 8 stories on 2026-09-24. No tile is "coming soon" any more. First-draft rubric. Tests: `tests/test_manufacturing_tile.py`. Live as `signals-deploy` `767ebfb`. | `git revert 6626dd1`, then rebuild and republish |
| BP-22 | `d5eb27d` | 2026-09-24 00:32 | **Live** | SupplyChainTile | Eighth tile made live, same rules (headline required, floor 5; "shortage", "port", "bottleneck", "UPS" at 2). The context rule: a housing, talent, water or cash "shortage" is not supply chain (a truck-driver shortage is). Software supply-chain attacks stay with Cyber; freight insurance with Insurance; India's UPS pension scheme is blanked. Holds 8 stories on 2026-09-24; FedEx's and Old Dominion's rate increases leave Banking and Global. Tests: `tests/test_supply_chain_tile.py`. Live as `signals-deploy` `767ebfb`. | `git revert d5eb27d` (after BP-23 if reverting both), then rebuild and republish |
| BP-21 | `12db981` | 2026-09-24 00:29 | **Live** | TelecomTile | Seventh tile made live, same rules (headline required, floor 5; "subscribers", "satellite", "ITU" at 2). Data centres count (the tile is Telecom & Digital Infrastructure). Airtel Money, Jio Financial, JioBlackRock and JioHotstar are blanked; Defence now blanks "submarine cable". The scraper drops Mobile World Live's French and Spanish republications. Holds 8 stories on 2026-09-24. Tests: `tests/test_telecom_tile.py`. Live as `signals-deploy` `767ebfb`. | `git revert 12db981` (after BP-22/23), then rebuild and republish |
| BP-20 | `393bb4d` | 2026-09-24 00:25 | **Live** | DomainFeeds | Trade-press feeds for the last three tiles: ET Telecom, RCR Wireless, Mobile World Live; Supply Chain Dive, The Loadstar, FreightWaves; Manufacturing Dive, ET Manufacturing (all tier 2 in `config/sources.yaml`). The scrape grows from 370 to about 500 articles; existing tiles only gain. Titles are unescaped once more (ET Telecom double-escapes "&amp;"). | `git revert 393bb4d` (after BP-21 to BP-23, which depend on it), then rescrape, rebuild and republish |
| BP-19 | `16f2d16` | 2026-09-24 00:05 | **Live** | ClimateTile | Sixth "coming soon" tile made live, with the same rules as Defence: the headline must name it, and bare "storm", "flood", "monsoon" and "rainfall" sit at 2 with a Climate floor of 5. Renewables and power stay with Energy; insured losses and cat bonds stay with Insurance. `NEUTRALIZE`: the business, political and investment "climate"; metaphorical storms, floods, droughts ("London's listing drought") and landslides; Cyber's Salt and Volt Typhoon hacker groups. Placed after Cyber, ahead of AI. Holds 8 stories on the 2026-09-23 scan, mostly extreme weather; Executive gives up a wildfire-liability story (7 to 6). First-draft rubric. Tests: `tests/test_climate_tile.py`. Live as `signals-deploy` `5449bb4`. | `git revert 16f2d16`, then rebuild and republish |
| BP-18 | `d62ee64` | 2026-09-23 23:58 | **Live** | CyberTile | Fifth "coming soon" tile made live, with the same rules as Defence: the headline must name it, and bare "privacy", "breach", "scam" and "hack" sit at 2 with a Cyber floor of 5. `NEUTRALIZE`: cyber insurance (cover, underwriting, claims, cat bonds, which are Insurance's), "Cyber Monday", "life hacks", "breach of contract", "Trojan horse". Takes "cyber defence", which Defence already blanks. Unambiguous names only ("Palo Alto Networks"; no "Wiz" or "Tenable"). Placed after Healthcare, ahead of AI. Holds 5 stories on 2026-09-23, 4 of them from AI's overflow; every other tile keeps its count. First-draft rubric. Tests: `tests/test_cyber_tile.py`. Live as `signals-deploy` `6461974`. | `git revert d62ee64`, then rebuild and republish |
| BP-17 | `936d870` | 2026-09-23 23:41 | **Live** | HealthcareTile | Fourth "coming soon" tile made live, with the same rules as Defence: the headline must name it, and bare "medical", "drug" and "patients" sit at 2 with a Healthcare floor of 5. `NEUTRALIZE`: health insurance, health insurers and COVID insurance claims (Insurance's), drug crime, computer viruses, "financial health", "pandemic-era" loans and metaphors. Unambiguous names only ("World Health Organization", not "WHO"). Placed after Defence, ahead of AI. Holds 2 stories on 2026-09-23, neither taken from another tile. First-draft rubric. Tests: `tests/test_healthcare_tile.py`. Live as `signals-deploy` `4dc164f`. | `git revert 936d870`, then rebuild and republish |
| BP-16 | `6440fa8` | 2026-09-23 23:29 | **Live** | PulseZeroWidth | Fix found while checking BP-15: a tab laid out at zero width (e.g. a hidden pane) showed Pulse's 2 leaders 4 times, because at width 0 every card "overflows". The loop now decides nothing until the row has a width and waits for the resize. Live as `signals-deploy` `07629b2`. | `git revert 6440fa8`, then rebuild and republish |
| BP-15 | `1f9d1f8` | 2026-09-23 23:23 | **Live** | DefenceTile | Third "coming soon" tile made live, with the same rules as Energy. `NEUTRALIZE`: sport ("title defence"), law ("defence lawyers", "self-defence"), metaphor ("army of", "secret weapon"), "Air Force One", veterans' personal stories, and cyber defence (Cyber's). Bare "defence" and "drone" at 2 with a Defence floor of 5 (`SIGNAL_FLOORS`), so neither qualifies alone. Placed after Energy, ahead of Global. Holds 4 stories on 2026-09-23. First-draft rubric. Tests: `tests/test_defence_tile.py`. Live as `signals-deploy` `3748930`. | `git revert 1f9d1f8` (after BP-16 if reverting both), then rebuild and republish |
| BP-14 | `eab25b1` | 2026-09-23 22:36 | **Live** | EnergyTile | Second "coming soon" tile made live, with the Banking review's rules built in: `TITLE_REQUIRED`, `NEUTRALIZE` (kitchen oils, tear gas, greenhouse gas, nuclear weapons and talks, shell companies, solar eclipses, energy drinks), companies in unambiguous forms only ("Shell plc", "BP plc"), and Indian-market terms (OMCs, LPG, CBG, discoms). Placed after Banking in `PRIORITY`. Holds 8 stories on 2026-09-23, none taken from another tile's top 8. First-draft rubric. Tests: `tests/test_energy_tile.py`. Live as `signals-deploy` `ee0f4cd`. | `git revert eab25b1`, then rebuild and republish |
| BP-13 | `6446cfb` | 2026-09-23 21:30 | **Live** | BankingRubric | Banking rubric review: `TITLE_REQUIRED` (the headline must carry a Banking keyword); `NEUTRALIZE` gains "banks on" as a verb and bank-branded insurers, fund houses and brokers (SBI Life, ICICI Lombard, HDFC AMC, Lloyd's…); bank results, payment-rail and central-bank vocabulary; 64 banks by name (19 Indian, 11 US, 18 European/UK, 16 Asia-Pacific/Middle East/Canada); investment banks at 2. Removes four false positives from the 2026-09-23 pool. Live as `signals-deploy` `582440a`. | `git revert 6446cfb` (after BP-14 if reverting both), then rebuild and republish |
| BP-12 | `3caca00` | 2026-09-23 20:38 | **Live** | PulseLoop | Fix for BP-10: Executive Pulse showed its 2 leaders twice on the live site. The loop now decides from the cards' natural width (flex-basis + gaps) rather than rounded scrollWidth, and re-decides on resize from the original cards. Live as `signals-deploy` `c367713`. | `git revert 3caca00`, then rebuild and republish |
| BP-11 | `fd69310` | 2026-09-23 20:29 | **Live** | BankingTile | First "coming soon" tile made live, on the same logic as the other tiles. New `signals.TILE_SIGNALS` (tile-only domains that compete only when `include_tile_signals=True`; the Signals page keeps its six), a Banking keyword list (first draft, to be reviewed), `NEUTRALIZE` (West Bank, World Bank, food bank and the like blanked before Banking is scored), and Banking placed after GCC and Insurance in `PRIORITY`. Tests: `tests/test_banking_tile.py`. Live as `signals-deploy` `bc4845d`. | `git revert fd69310` (after BP-12 if reverting both), then rebuild and republish |
| BP-10 | `548eb99` | 2026-09-23 20:09 | **Live** | PeopleRows | Final page rows now run: engine tiles (all 14, self-scrolling) → Featured Analysis (GCC → Insurance → Global) → People Movers → Executive Pulse → Leaders on Record. The Global/Economy/AI card row and `_hero` are removed. New `app/scraper/leader_quotes.py` and `config/leader_quotes.yaml` (verbatim quotes from newsrooms, press and Anthropic's news page, cached in `instance/`). New `build_movers`, `build_record`, `build_people_rows` in `command_center.py`. Pulse is limited to corporate roles, and each person appears once (Movers > Record > Pulse). Movers, Pulse and Record cards widen to fill their row. Tests: new `tests/test_people_rows.py`; row tests in `test_freshness_gate.py` rewritten. Live as `signals-deploy` `104a533`. | `git revert 548eb99`, then restore the live site to `14a1957` (see *Live site*) or run the *Build Signals* workflow |
| *BP-09 (pending)* | — | 2026-09-23 | **Local** | Hero animation + top-rows previews | Two untracked preview folders. `docs/design_previews/2026-09-23-hero-signal/`: the `GlobalSignalAnimation` demos (Orbital, Engine, Pipeline), the Demo 4 redesign `IntelligenceField` (canvas), and Final-page placement previews. `docs/design_previews/2026-09-23-rows/`: the agreed four-row top (self-scrolling engine row, Featured Analysis, People Movers, Leaders on Record), generated from the live cache, plus `quotes_probe.py`, which reads company newsrooms and technology press for verbatim leader quotes. `docs/design_previews/index.html` is a hub page linking every preview. None of it touches the live page. | Not committed. Delete the folders to discard them. |
| BP-08 | `2bb31d3` | 2026-09-23 11:55 | **Live** | TileImages | Articles on the Command Center that arrive without a feed image now take their page's `og:image`, skipping publisher logo cards. Fixed the Insurance tile never showing a photo. New `app/scraper/article_images.py` and tests; used in the build script and `/api/command-center`. | `git revert 2bb31d3`, then rebuild data and republish (see *Live site*) |
| BP-07 | `939fb4a` | 2026-09-23 11:42 | **Live** | DeployRoot | The daily workflow now publishes the Command Center as the root of `signals-deploy` (the branch Vercel serves) and moves the Signals page to `/signals`. This made the site link open the dashboard instead of Signals. | `git revert 939fb4a`, **and** restore the live site to `5dc48b9` (see *Live site*) |
| BP-06 | `f5b6c3e` | 2026-09-23 10:44 | **Live** | CommandCenterLayout | Front-door changes: tiles first, quieter page chrome, "Know What Matters" hero kicker, nine new tile vectors. Authored in `command_center_source.html`, rebuilt into the template and `public/`. | `git revert f5b6c3e` (then rebuild `public/` and republish) |
| BP-05 | `498cb83` | 2026-09-23 10:44 | Pushed | KeywordMiner | Proposes new GCC keywords from accumulated history, using lift and coverage instead of raw word frequency. Adds a tool and tests; changes no live classification. | `git revert 498cb83` |
| BP-04 | `238c964` | 2026-09-23 09:57 | **Live** | GCCRubric | GCC classification now needs two independent kinds of evidence, so place names (Noida, Gurugram) can no longer classify a story alone. Also rebuilt the Command Center page and data files. | `git revert 238c964` (after BP-06/BP-08 if you're reverting those too), then rebuild and republish |
| BP-03 | `094e8b4` | 2026-09-23 09:25 | **Live** | StaticBuild | Carries TileSync into the source template (`command_center_source.html`) so the next build doesn't silently undo it, then rebuilds `public/`. | Revert **together with** BP-02: `git revert 094e8b4 a655666`, then republish |
| BP-02 | `a655666` | 2026-09-23 09:11 | **Live** | TileSync | Each tile's picture follows the headline it's showing, replacing one fixed photo under all five headlines. | Revert with BP-03 (above) |
| BP-01 | `d82d6d6` | 2026-09-21 16:58 | **Live** | GCCFix | "India"/"Indian" alone no longer classify a story as Signal GCC. Affects which stories reach the live GCC tile. | `git revert d82d6d6`, then rebuild data and republish |

**Dependencies to respect when rolling back**
- **Revert newest first.** BP-02/03, BP-04, BP-06, BP-08 and BP-10 to BP-23 all touch the Command Center page (`command_center_source.html`, the template, `public/`). Reverting an older one on its own will likely conflict.
- BP-02 and BP-03 go together; reverting only one leaves the source template and the generated page out of step.
- BP-04 and BP-01 both change the GCC rules in `app/analysis/signals.py`. Revert BP-04 first if you revert both.
- Reverting a **Live** breakpoint doesn't change the website until `signals-deploy` is republished: run the *Build Signals* workflow, or push a rebuilt tree.

---

## Baseline milestones (before the BP series)

Earlier stable points, if you ever need to go further back. The hash is the last commit of each phase.

| Milestone | Last commit | Date | Branch pointer | What it contains |
|---|---|---|---|---|
| Sprint 10 + updates | `a14aa5b` | 2026-09-20 | — | Developments ("one story, one slot") and a 24-file update pass. Last state before BP-01. |
| Intelligence pipeline, sprints 0–8 | `1729319` | 2026-07-28 | `feat/intelligence-pipeline` | Test harness and gold set, source trust, freshness, domains, entities, events, impact scoring, priority bands, labelling guide |
| Live Command Center | `9d9cc99` | 2026-07-26 | `Main` (local) | Command Center bound to live data; each tile cycles its top 5 articles. `origin/Main` is one commit behind, at `e6ff8ac`. |
| Landing hero + classification fixes | `0f10d58` | 2026-07-26 | — | Animated hero, MetLife branding removed, GCC/Executive routing fixes, mojibake fix |
| Foundation + first Vercel deploy | `d7e84d5` | 2026-07-25 | — | Signals page, LinkedIn publishing, production hardening, `signals-deploy` publishing |

---

## Live site (`signals-deploy` → news-letter-cxo.vercel.app)

The workflow force-pushes this branch daily, so its history is short. Keep this list; it's the only record of earlier live states.

| Live state | Commit | Published | What visitors saw |
|---|---|---|---|
| **Current** | `767ebfb` | 2026-09-24 00:37 | BP-20 to BP-23: Telecom, Supply Chain and Manufacturing tiles live, with their new feeds (all 14 tiles live) |
| Previous | `5449bb4` | 2026-09-24 00:06 | BP-19: Climate tile live (11 live tiles, 3 coming soon) |
| Earlier | `6461974` | 2026-09-23 23:58 | BP-18: Cyber tile live (10 live tiles, 4 coming soon) |
| Earlier | `4dc164f` | 2026-09-23 23:41 | BP-17: Healthcare tile live (9 live tiles, 5 coming soon) |
| Earlier | `07629b2` | 2026-09-23 23:29 | BP-16: Pulse zero-width guard, on top of the BP-15 Defence tile (8 live tiles) |
| Earlier | `3748930` | 2026-09-23 23:23 | BP-15: Defence tile live |
| Earlier | `ee0f4cd` | 2026-09-23 22:36 | BP-14: Energy tile live (7 live tiles) |
| Earlier | `582440a` | 2026-09-23 22:28 | BP-13: Banking rubric review |
| Earlier | `c367713` | 2026-09-23 20:38 | BP-12: Executive Pulse loop fix, on top of the BP-11 Banking tile |
| Earlier | `bc4845d` | 2026-09-23 20:29 | BP-11: Banking tile live; Pulse could still show duplicate cards |
| Earlier | `104a533` | 2026-09-23 20:09 | BP-10 layout: engines → Featured → People Movers → Executive Pulse → Leaders on Record; Signals at `/signals` |
| Earlier | `14a1957` | 2026-09-23 11:55 | Command Center at `/` with recovered tile images (BP-08), Signals at `/signals` |
| Earlier | `280ee29` | 2026-09-23 11:42 | Command Center at `/` (BP-07), Signals at `/signals` |
| Pre-DeployRoot | `5dc48b9` | 2026-07-25 | The Signals page only, at `/`. **Only in the local reflog; git will eventually clean it up.** Preserve it with `git tag live-pre-deployroot 5dc48b9`. |

**Roll the live site back to an earlier state.** This rewrites the deploy branch, so do it deliberately:

```bash
git push --force origin <commit>:refs/heads/signals-deploy
```

Also revert the matching code breakpoint (for example BP-07). Otherwise the next daily build republishes the newer state.

---

## Rollback recipes

**Look at a breakpoint without changing anything**
```bash
git switch --detach <commit>
```
Return with `git switch final`.

**Undo a pushed breakpoint (safe, keeps history)**
```bash
git revert <commit>
```
Then push `final`. Use this for anything at stage **Pushed** or **Live**.

**Move `final` back to a breakpoint (discards everything after it)**
```bash
git reset --hard <commit>
```
Only for **Committed** (unpushed) work. For pushed work it needs a force-push that rewrites shared history, so tag the current head first: `git tag before-rollback`.

---

## Adding a new breakpoint

1. Commit with the next ID in the subject, e.g. `BP-09 HeroAnimation: …`.
2. Add a row to the top of the breakpoints table, with its stage and rollback command.
3. When it's pushed, and again when it's live, update the **Stage** column.
