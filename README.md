# BB Lightweight Inventory

Internal inventory tracker for [Bourbon Baggers](https://bourbonbaggers.com) — a small
craft spirits brand. Tracks product and supply quantities across four physical locations
(storage unit, garage, trailer, office) plus an inbound queue for in-transit shipments.

Built to be used one-handed on an iPhone while standing in a hot Texas garage.

## Stack

- **Backend:** Python + FastAPI
- **Database:** SQLAlchemy + SQLite (schema is Postgres-ready)
- **Templates:** Jinja2 (server-side rendering)
- **Frontend:** Tailwind CSS via CDN, Alpine.js via CDN
- **Deployment:** Docker Compose
- **Auth:** Cloudflare Access (Google SSO) — zero auth in the app itself

## Features

- Four item categories: Products, Components, Shipping Boxes, Other
- Products support a carton → case → unit hierarchy with optional filled/unfilled states
- Location view with per-category accordions and an "Add Item" modal
- Count entry with live unit conversion display
- Inbound location with carrier/tracking and receive-and-distribute flow
- Cross-location totals and count history per product
- Full REST API at `/docs` — built for eventual LLM/voice integration
- PWA-installable from Safari (standalone mode, no browser chrome)

## Running locally

Requires Docker Desktop.

```bash
cp .env.example .env        # defaults work out of the box
docker-compose up --build   # app starts at http://localhost:8001
docker-compose exec app python scripts/seed.py   # seed locations + starter products
```

## Deploying

```bash
ssh user@your-vm
git clone https://github.com/BourbonBaggers/bb-lightweight-inventory.git
cd bb-lightweight-inventory
# copy .env from your local machine — never commit it
docker compose up --build -d
docker compose exec app python scripts/seed.py
```

Subsequent deploys:

```bash
git pull && docker compose up --build -d
```

## Project layout

```
app/
├── main.py              # FastAPI entry point, router wiring
├── database.py          # SQLAlchemy engine + session
├── models.py            # ORM models: Location, Product, InventoryCount
├── services/            # Business logic (inventory math, CRUD)
├── routes/
│   ├── api/             # JSON endpoints — the interface an agent would use
│   └── pages/           # Server-rendered page routes
└── templates/           # Jinja2 HTML templates
scripts/
└── seed.py              # Idempotent seed for locations + starter products
docs/
├── REQUIREMENTS.md      # Full product requirements
└── PLAN.md              # Build plan with phase-by-phase git checkpoints
```

## Design notes

**API-first:** Every inventory mutation goes through a REST endpoint. Templates are
display-only. This means a voice/LLM layer can call the same API the UI uses without
any backend changes.

**Append-only counts:** `InventoryCount` records are never updated — only inserted. Current
quantity = most recent record for a (product, location, state) combination. History is free.

**No in-app auth:** Cloudflare Access handles authentication entirely. Adding login screens
would be redundant and annoying for a one-user app.
