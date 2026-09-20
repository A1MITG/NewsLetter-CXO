# Command Center — design previews, archived 2026-07-27

Frozen snapshot of two competing layout directions for the Command Center,
kept so we can flip back to them later. **Nothing here is wired into the app
or deployed** — this folder is documentation, deliberately kept out of
`public/` so Vercel never publishes it.

## What's here

| File | What it is |
|---|---|
| `preview_a.html` | **Concept A — Executive Dashboard** (Bloomberg-inspired). Status-bar nav, left engine rail with live counts, filterable centre story stack, right Executive Pulse column. Includes a dark-terminal toggle. |
| `preview_c.html` | **Concept C — current design, evolved.** Keeps the existing band rhythm; adds a collapsible hero, a live-bound Featured block, and collapses the 9 unscored engines from full tiles to chips. |
| `engine_icons.js` | `ENGINE_ICONS` + `ENGINE_ORDER`, extracted verbatim from `public/command_center.html` (lines 639–788 at commit `9d9cc99`) so both previews render the real animated engine icons. |
| `command_center_data.json` | The exact data snapshot both previews were built against. Frozen on purpose — see *Data vintage* below. |

**Concept B — Editorial Briefing** (FT/McKinsey-inspired) was designed as an
ASCII wireframe only and never built, because it is a prose-led layout and the
pipeline has no prose to give it. See *Why B wasn't built*.

## The third option: the current live page

Not duplicated here — it is 2.4 MB, mostly base64 images, and already tracked
in git unmodified. To retrieve the exact baseline these were compared against:

```bash
git show 9d9cc99:public/command_center.html > /tmp/command_center_baseline.html
```

## How to run them

Both previews `fetch()` their data with a relative path, so they need to be
served over HTTP — opening them as `file://` will fail with a CORS error.

```bash
cd docs/design_previews/2026-07-27
python -m http.server 8001
```

Then open <http://localhost:8001/preview_a.html> and
<http://localhost:8001/preview_c.html>.

To compare against the live page at the same time, serve `public/` on a
second port:

```bash
cd public && python -m http.server 8000   # -> localhost:8000/command_center.html
```

### Things to interact with

- **Preview A** — click engines in the left rail to filter the centre stack;
  *Toggle dark terminal* in the yellow bar switches the theme.
- **Preview C** — *Show returning-visitor state* collapses the hero to an
  88px strip, which is the core proposal of that concept.

## Data vintage — read before judging freshness

`command_center_data.json` here is the **2026-07-26** build
(`instance/articles_cache.json` was stamped `"date": "2026-07-26"`), archived
on 2026-07-27. It is frozen deliberately so these previews keep rendering the
same headlines regardless of when they're reopened.

## Known issues in both previews

1. **Both previews display the browser's current date, not the data's date.**
   Preview C renders `new Date()` into the TODAY divider; Preview A does the
   same in the status-bar clock and stamps every story row `TODAY`. Against
   this frozen snapshot they will always claim the data is from whenever you
   happen to open them. This is the same "asserting unearned freshness"
   problem the project has been removing elsewhere. **Whichever concept is
   adopted must carry a `date` field through from the cache into
   `command_center_data.json` and render that, with a visible "as of" marker
   when it isn't today.**

2. **Image wells are placeholders**, stamped `curated image`. The pipeline
   produces no images; the current live page's images are hand-picked.

3. **Executive Pulse items are hand-picked**, tagged
   `curated · not pipeline-selected`. They are real articles with real URLs,
   chosen in an earlier session — not selected by any scoring engine. This is
   the section most dependent on the unresolved commentary-generation
   decision.

4. **No Signal Executive engine.** `command_center_data.json` has no
   `executive` key, so Preview A's rail shows 5 live engines, not 6. Still an
   open gap.

5. **Engine icon animations are static.** The icon SVGs rely on keyframes
   defined in the live page's `<style>` block, which was not extracted.

## Why B wasn't built

Reference research (Fox News fetched live; Bloomberg via published design
writeups) showed that news homepages run *category tag + headline + source*,
with summaries the exception. That is exactly the shape of the current data —
`title` and `url` only. An editorial layout is mostly whitespace and prose;
with no prose available it would either render as bare links adrift in white
space, or require hand-written copy, which is the practice being removed from
this project. B stays parked until a commentary-generation decision is made.

## Status

No decision made as of 2026-07-27. `public/command_center.html` is untouched.
