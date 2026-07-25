# SIGNAL — Insurance & CXO Intelligence

SIGNAL scrapes insurance-trade, business, and geopolitical news, scores each
article against a weighted-keyword framework, and publishes two daily views:

- **The Daily Brief** (`/`) — a five-lens executive brief (Macro & Geo-Political,
  Regulatory & Compliance, Economic & Market, Digital/AI & Automation,
  Operating Model & Talent).
- **Signals** (`/signals`) — the same articles regrouped under six audience-facing
  Signals (Global, Business, AI, GCC, Insurance, Executive), rendered in a
  Bloomberg-terminal-style layout.

A companion script can also publish a condensed version of the Daily Brief to
LinkedIn.

## Architecture

```
app/
  analysis/
    scorer.py      Keyword-weighted scoring engine for the five-lens Daily Brief
    signals.py      Weighted-evidence classifier for the six Signals (with
                     near-duplicate suppression and disambiguation rules)
    synthesis.py     Turns scored articles into the Daily Brief JSON structure
  api/
    routes.py        Flask blueprint: /api/newsletter, /api/signals
  scraper/
    sources.py        Registry of RSS/HTML sources, grouped by geography/beat
    scraper.py         Async fetch + parse (RSS and HTML fallback), NewsAPI
    store.py           Once-a-day on-disk cache shared by both views
  static/               style.css (Daily Brief), signal.css (Signals terminal theme)
  templates/            index.html, signals.html
  main.py                Flask app factory and routes
config/
  config.py              Flask config, reads secrets from environment variables
  env_check.py           Startup validation: fails fast if production is misconfigured
.github/workflows/
  ci.yml                 Runs on every push/PR: install, compile check, import check, tests
scripts/
  run_scraper.py         Manual one-off scrape, for debugging sources
  linkedin_auth.py        One-time OAuth flow; writes a LinkedIn access token to .env
  daily_linkedin_post.py  Scrapes, synthesizes, and posts the brief to LinkedIn
docs/
  SIGNAL_Pipeline_Pseudocode.docx  Full scoring/classification pipeline reference
tests/                    Unit tests for the scorer and scraper module
instance/                 Runtime-only: the daily articles_cache.json (not committed)
```

### How article flow works

1. `scraper.py` fetches every source in `sources.py` in parallel (RSS parsed as
   XML, everything else as an HTML link scrape), plus NewsAPI if a key is set.
2. `store.py` caches the result once per calendar day in
   `instance/articles_cache.json`. Every request that day is served from that
   cache; if a fresh scrape ever returns nothing, the previous day's cache is
   served instead of an empty page.
3. `synthesis.py` (Daily Brief) and `signals.py` (Signals) each independently
   score and bucket the same cached articles — two different lenses on one
   dataset.

## Local setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env          # then fill in the values you need
python -m app.main
```

Open `http://127.0.0.1:5000/` and `http://127.0.0.1:5000/signals`.
`http://127.0.0.1:5000/health` returns `{"status": "ok"}` for uptime checks.

Force a fresh scrape (bypassing the daily cache) by appending `?refresh=1` to
either API endpoint.

## Environment variables

See `.env.example` for the full list with descriptions. Summary:

| Variable | Required | Purpose |
|---|---|---|
| `APP_ENV` | No (defaults to `development`) | Set to `production` on real deployments — see Security below |
| `SECRET_KEY` | **Yes, when `APP_ENV=production`** | Flask session signing key. Dev has a safe, clearly-labeled fallback |
| `NEWS_API_KEY` | No | Adds NewsAPI.org results to the scrape |
| `LINKEDIN_CLIENT_ID` / `LINKEDIN_CLIENT_SECRET` | Only for LinkedIn posting | From your LinkedIn developer app |
| `LINKEDIN_ACCESS_TOKEN` / `LINKEDIN_PERSON_URN` | Only for LinkedIn posting | Written automatically by `linkedin_auth.py` |

Never commit `.env` — it's git-ignored. `.env.example` documents the shape
without any real values. Every variable is validated once at startup by
`config/env_check.py`: missing optional variables log a warning naming the
feature they disable; a missing `SECRET_KEY` when `APP_ENV=production` raises
immediately and refuses to start, rather than silently running with an
insecure key.

## LinkedIn posting

```bash
python scripts/linkedin_auth.py            # one-time browser authorization
python scripts/daily_linkedin_post.py --dry-run   # preview without publishing
python scripts/daily_linkedin_post.py             # publish
```

The LinkedIn access token expires roughly every 60 days; rerun
`linkedin_auth.py` when posting starts failing with an auth error.

## Tests

```bash
python -m unittest discover -s tests -v
```

`.github/workflows/ci.yml` runs this, plus a dependency install and a compile
check across every tracked `.py` file, on every push and pull request.

## Publishing the Signals page to Vercel (static)

`/signals` alone can be published to Vercel as a static site — this sidesteps
the serverless/local-cache mismatch described below entirely, because Vercel
never runs Python for it; it only serves pre-built files.

- `scripts/build_static_signals.py` scrapes fresh, renders the real
  `signals.html` template once, and writes `public/index.html`,
  `public/signals.json`, and `public/signal.css`.
- `.github/workflows/build-signals.yml` runs that script daily at 08:00 IST
  (and on-demand via its "Run workflow" button), then commits `public/` back
  to the repo if it changed. Pushing to the connected branch is what
  triggers Vercel's redeploy — no Vercel token needed in GitHub.
- `vercel.json` sets `outputDirectory: public` and disables any build step,
  since the static files already arrive pre-built.

To connect it: import the repo in the Vercel dashboard, leave the framework
preset as "Other" (it will pick up `vercel.json` automatically), and deploy.
The page updates once a day on the schedule above; there is no live
`?refresh=1` for this static build — use the workflow's manual "Run
workflow" button to force an early rebuild.

This only covers `/signals`. The Daily Brief (`/`) and the LinkedIn script
still need the always-on Flask app described below.

## Deployment notes

This is a standard Flask app with two stateful assumptions that matter for
hosting: it writes a daily JSON cache to local disk (`instance/`), and the
scrape itself is a multi-minute background-style operation triggered by the
first request of the day. That combination fits a conventional always-on host
with persistent disk (a VPS, Render, Railway, Azure/AWS App Service, or a
Docker container with a mounted volume) far better than a stateless serverless
platform — on serverless, the local cache won't persist between invocations
and a cold-started function may not have time to complete a full scrape.

For an always-on host:

```bash
pip install -r requirements.txt
gunicorn "app.main:app"      # or another production WSGI server
```

Set all required environment variables on the host (never hardcode them), and
mount/persist the `instance/` directory so the daily cache survives restarts.
