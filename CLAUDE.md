# BB Lightweight Inventory

## Project Overview
Simple internal inventory quantity tracker for Bourbon Baggers (solopreneur — Jay + wife).
Tracks product and packaging counts across four physical locations:
- Storage unit
- Garage
- Trailer
- Office

**What this is:** Know how much stuff you have and where, so you can reorder when running low.
**What this is not:** Accounting software. No COGS, no cost/value tracking, no purchase history,
no order integration, no automatic reorder alerts, no barcode scanning (initial scope).

Usage pattern: visual count ~once/week, entered on iPhone while physically at the location.

## Stack
- **Backend:** Python 3.x + FastAPI
- **ORM/DB:** SQLAlchemy + SQLite (schema designed for zero-friction Postgres migration later)
- **Templates:** Jinja2 (server-side rendering, no build pipeline)
- **CSS:** Tailwind CSS via CDN
- **JS:** Alpine.js via CDN
- **Deployment:** Docker Compose
- **Version control:** GitHub (public repo)

## Key Directories

```
app/
├── main.py          # FastAPI app entry point
├── database.py      # SQLAlchemy engine + session
├── models.py        # ORM models (Items, Locations, InventoryCounts)
├── routes/          # FastAPI routers, one file per domain
├── templates/       # Jinja2 HTML templates
└── static/          # Any static assets not served via CDN
scripts/             # Utility and maintenance scripts
tests/               # Test suite
docker-compose.yml   # Deployment config
Dockerfile
.env.example         # Template for required env vars (never commit .env)
```

## Dev Workflow
**Mac = dev. Ubuntu 26.04 VM on Proxmox = prod. No staging.**

Local development:
```bash
docker-compose up --build        # start
docker-compose down              # stop
docker-compose logs -f           # watch logs
```

Deploy to prod:
```bash
ssh <ubuntu-vm>
git pull
docker-compose up --build -d
```

## Security
- **Zero auth in the app.** No login screens, no sessions, no tokens.
- **Cloudflare Access** is the sole auth layer: Google SSO, info@boozebaggers.com only, long cookie.
- Never add an in-app authentication system — it would be redundant and annoying.
- Secrets (if any) go in `.env`, which is gitignored. Use `.env.example` for the template.

## UX Constraints — Read Before Touching Any Template
Primary use: **iPhone, one-handed, in a hot Texas garage or storage unit.**

Every UI decision must pass this filter:
- Large tap targets — nothing small or precise
- Thumb-reachable layout — critical actions in the bottom 2/3 of the screen
- High contrast — readable in direct sunlight
- Minimal typing — prefer number inputs with +/− controls over free-text fields,
  but allow direct number entry (don't force 25 taps to enter 25)
- Fast — no heavy assets, no unnecessary round trips
- Functional over beautiful — clean, not award-winning

## Rules

### Code Style
- No comments unless the WHY is non-obvious
- No multi-line docstrings or comment blocks
- No error handling for scenarios that can't happen — trust internal guarantees
- No abstractions, refactors, or features beyond what the task requires
- SQLAlchemy models must remain DB-agnostic (no SQLite-specific syntax) to preserve Postgres migration path
- **Templates and markup live in files, never in Python.** HTML goes in `.html` Jinja2 template files,
  CSS in `.css` files. Never assign multi-line HTML/CSS to a Python variable as an escaped string.
  If you're tempted to write `content = "<div>...</div>"` — stop and make a template file instead.
- **API-first architecture.** Every inventory mutation goes through a REST endpoint (JSON).
  Templates are display-only. Business logic lives in `app/services/`, not in route handlers
  or templates. Route handlers are thin: validate → call service → return. This keeps the
  system agent-ready — an LLM can call the same endpoints the UI uses without any backend changes.
- **Shared logic belongs in helpers, not repeated inline.** Before writing date manipulation,
  formatting, parsing, or any general-purpose logic, check if a utility function already exists.
  Common operations go in a shared module (e.g. `app/utils.py`) and are reused, not re-implemented
  file after file. Name helpers so their purpose is obvious without reading the body.

### Git
- Never commit unless explicitly asked
- Never force-push, reset --hard, or run destructive git ops without confirmation
- Never skip hooks (--no-verify)
- .env is gitignored — never commit secrets

### Responses
- No emojis unless explicitly requested
- Concise — one sentence of context, then the work
- No trailing summaries of what was just done

### What Not To Build
Never suggest or add these — they are explicitly out of scope:
- Automatic reorder alerts or notifications
- Cost, value, or COGS tracking
- Purchase history or order integration
- Barcode scanning (not initial scope — revisit only if asked)
- In-app authentication of any kind
- Offline/sync capability
- Reporting dashboards or data exports

## Future Scope (Do Not Build Yet)
- **Voice / LLM integration:** microphone → speech → LLM parses → calls existing REST API
  endpoints. API-first architecture means this drops in without backend changes.
- **Barcode scanning** via iPhone camera
