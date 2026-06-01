# BB Lightweight Inventory — Build Plan

This file is the canonical build plan. It persists across sessions so work can resume
after context limits, reloads, or interruptions. Each phase ends with a git commit —
read the log to find where we left off.

**How to resume:** Run `git log --oneline` and find the last phase commit. Pick up at
the next unchecked phase below.

---

## Git Setup (one-time, before Phase 0)

- [ ] `git init` in project root
- [ ] Create `.gitignore` (Python, Docker, macOS, .env)
- [ ] Initial commit: `"chore: init repo with CLAUDE.md, requirements, plan"`

---

## Phase 0 — Project Scaffolding

**Goal:** Runnable empty FastAPI app in Docker. Nothing works yet — just the skeleton boots.

### Tasks
- [ ] `requirements.txt` — FastAPI, Uvicorn, SQLAlchemy, Jinja2, python-dotenv
- [ ] `Dockerfile` — Python 3.12-slim, installs deps, runs uvicorn
- [ ] `docker-compose.yml` — mounts `./data` volume for SQLite, exposes port 8001 (avoids conflict with timecard on 8000)
- [ ] `app/__init__.py`
- [ ] `app/main.py` — bare FastAPI app, mounts static, includes routers (stubs), sets up Jinja2
- [ ] `app/database.py` — SQLAlchemy engine from `DATABASE_URL`, session factory, `Base`
- [ ] Directory placeholders: `app/routes/`, `app/services/`, `app/templates/`, `app/static/`, `data/`
- [ ] `.env` from `.env.example` (local only, gitignored) — update PORT to 8001
- [ ] Verify: `docker-compose up --build` boots without error, `curl localhost:8001` returns something

### Commit
```
chore(phase-0): project scaffolding — Docker + bare FastAPI boots
```

---

## Phase 1 — Data Models

**Goal:** All three SQLAlchemy models defined. Tables auto-created on startup. No routes yet.

### Tasks
- [ ] `app/models.py`:
  - [ ] `Location` — id, name, default_unit (enum: carton/case/unit), is_inbound (bool, default False)
  - [ ] `Product` — id, name, category (enum: product/product_packaging/other), has_states (bool),
        cases_per_carton, units_per_case, filled_cases_per_carton, filled_units_per_case,
        unfilled_cases_per_carton, unfilled_units_per_case, packaging_unit_label, is_active (bool, default True)
  - [ ] `InventoryCount` — id, product_id (FK), location_id (FK), state (enum: filled/unfilled/null),
        cartons_qty, cases_qty, units_qty, counted_at (datetime, default now), is_approximate (bool),
        cpc_snapshot, upc_snapshot, notes, carrier, tracking_number
- [ ] `app/database.py` — call `Base.metadata.create_all()` on startup
- [ ] Verify: container starts, SQLite file created in `data/`, tables visible via `sqlite3`

### Commit
```
feat(phase-1): SQLAlchemy models — Location, Product, InventoryCount
```

---

## Phase 2 — Seed Data

**Goal:** The five known locations and a handful of starter products exist in the DB so
every subsequent phase has real data to render against.

### Tasks
- [ ] `scripts/seed.py` — idempotent (skip if data exists):
  - [ ] Locations: Storage Unit (carton), Garage (case), Trailer (unit), Office (unit), Inbound (unit, is_inbound=True)
  - [ ] Products: at minimum 2–3 across categories (1 product with has_states=True, 1 product_packaging, 1 other)
- [ ] Run seed inside container: `docker-compose exec app python scripts/seed.py`
- [ ] Verify: rows in DB

### Commit
```
chore(phase-2): seed script — five locations + starter products
```

---

## Phase 3 — Service Layer

**Goal:** All business logic isolated in `app/services/`. No templates or routes yet —
just importable functions with correct logic.

### Tasks
- [ ] `app/services/__init__.py`
- [ ] `app/services/locations.py`:
  - [ ] `get_all_locations()` → list
  - [ ] `get_location(id)` → Location or 404
  - [ ] `create_location(data)` → Location
  - [ ] `update_location(id, data)` → Location
  - [ ] `delete_location(id)` → ok / error if counts exist
- [ ] `app/services/products.py`:
  - [ ] `get_all_products(active_only=True)` → list
  - [ ] `get_product(id)` → Product or 404
  - [ ] `create_product(data)` → Product
  - [ ] `update_product(id, data)` → Product
  - [ ] `deactivate_product(id)` → Product (soft delete, is_active=False)
- [ ] `app/services/inventory.py`:
  - [ ] `current_count(product_id, location_id, state)` → latest InventoryCount or None
  - [ ] `current_counts_for_location(location_id)` → list of latest counts (non-zero only)
  - [ ] `current_counts_for_product(product_id)` → list across all locations (non-zero)
  - [ ] `total_units(count)` → int using cpc_snapshot × upc_snapshot × qty math
  - [ ] `save_count(product_id, location_id, state, cartons, cases, units, **kwargs)` → InventoryCount
  - [ ] `items_not_at_location(location_id)` → active products with zero current count there
  - [ ] `history_for_product(product_id, limit=20)` → list
  - [ ] `receive_inbound(inbound_count_id, received_qty, received_unit, distribution)` → ok
        (distribution = dict of {location_id: qty}; creates destination counts, updates inbound remainder)

### Commit
```
feat(phase-3): service layer — locations, products, inventory logic
```

---

## Phase 4 — REST API Routes (JSON)

**Goal:** Every mutation has a JSON endpoint. The UI will call these. `/docs` works.

### Tasks
- [ ] `app/routes/api/locations.py`:
  - [ ] `GET /api/locations` — list all
  - [ ] `POST /api/locations` — create
  - [ ] `PUT /api/locations/{id}` — update
  - [ ] `DELETE /api/locations/{id}` — delete
- [ ] `app/routes/api/products.py`:
  - [ ] `GET /api/products` — list (optional ?active=true)
  - [ ] `POST /api/products` — create (with optional initial inventory records)
  - [ ] `PUT /api/products/{id}` — update
  - [ ] `DELETE /api/products/{id}` — soft delete
- [ ] `app/routes/api/inventory.py`:
  - [ ] `GET /api/inventory/location/{location_id}` — current counts for location
  - [ ] `GET /api/inventory/product/{product_id}` — current counts for product (all locations)
  - [ ] `POST /api/inventory/count` — save a new count entry
  - [ ] `POST /api/inventory/receive` — receive inbound (distribute + update remainder)
  - [ ] `GET /api/inventory/history/{product_id}` — count history
  - [ ] `GET /api/inventory/not-at-location/{location_id}` — items with zero count here
- [ ] Wire all routers into `app/main.py`
- [ ] Verify: `/docs` renders all endpoints; test a POST via Swagger UI

### Commit
```
feat(phase-4): REST API routes — all JSON endpoints, /docs working
```

---

## Phase 5 — Base Template + App Shell

**Goal:** Every page shares a base layout. Sidebar nav works. PWA is installable.

### Tasks
- [ ] `app/templates/base.html`:
  - [ ] `<head>`: Tailwind CDN, Alpine.js CDN, PWA meta tags
        (`apple-mobile-web-app-capable`, `apple-mobile-web-app-status-bar-style`,
        `viewport` with `viewport-fit=cover`)
  - [ ] Hamburger icon — top-left, fixed, always visible
  - [ ] Slide-out sidebar (Alpine.js `x-show` + transition):
    - Dashboard link
    - Locations group (expandable ▾) — populated from DB
    - Products group (expandable ▾) — Products / Product Packaging / Other
    - Reports group (expandable ▾) — Count History
    - Settings group (expandable ▾) — Manage Products / Manage Locations
  - [ ] Tap-outside-to-close overlay
  - [ ] Active item highlighting (Jinja2 `request.url.path` check)
  - [ ] Main content `{% block content %}{% endblock %}`
- [ ] `app/static/manifest.json` — name, short_name, display: standalone, theme_color, icons
- [ ] `app/static/sw.js` — install event only, no caching (per requirements)
- [ ] `app/static/icon-192.png`, `icon-512.png` — simple placeholder icons (can be updated later)
- [ ] Register service worker in base template `<script>`
- [ ] Page route `GET /` → renders a stub template extending base (placeholder until Dashboard done)
- [ ] Verify: loads in Safari, "Add to Home Screen" works, opens full-screen standalone

### Commit
```
feat(phase-5): base template — sidebar nav, hamburger, PWA manifest + service worker
```

---

## Phase 6 — Dashboard

**Goal:** Default landing page. Shows cross-location totals and location summaries.

### Tasks
- [ ] `app/routes/pages/dashboard.py` — `GET /` queries totals via service layer, renders template
- [ ] `app/templates/dashboard.html` extends base:
  - [ ] Products accordion — "Products (X items)", each row: name + total filled/unfilled units; tap → Product Detail
  - [ ] Product Packaging accordion — "Product Packaging (X items)", name + total qty; tap → Product Detail
  - [ ] Other accordion — "Other (X items)"; tap → Product Detail
  - [ ] Locations summary (always visible) — location name + item count; tap → Location View
  - [ ] All accordions collapsed by default (Alpine.js)
- [ ] Verify: real data renders, accordions open/close, tapping a row navigates

### Commit
```
feat(phase-6): dashboard — inventory totals + location summary
```

---

## Phase 7 — Location View

**Goal:** Per-location item list. Add Item modal. Inbound-specific UI.

### Tasks
- [ ] `app/routes/pages/locations.py` — `GET /locations/{id}` renders location view
- [ ] `app/templates/location.html` extends base:
  - [ ] Header: location name
  - [ ] "+ Add Item" button (top right)
  - [ ] Products accordion — non-zero items; has_states=True → 2 rows (Filled/Unfilled); tap row → Count Entry
  - [ ] Product Packaging accordion — non-zero items; tap row → Count Entry
  - [ ] Other accordion — tap row → Count Entry
  - [ ] Approximate counts shown with `~` prefix
  - [ ] **If inbound location:** carrier + tracking shown per item; "Receive" button per item → Receive screen
  - [ ] "+ Add Item" modal sheet:
    - Search bar (Alpine.js live filter)
    - Items grouped by category (items with zero count at this location)
    - "+ Create new product" row at bottom → Product Catalog add form, then Count Entry

### Commit
```
feat(phase-7): location view — item lists, add item modal, inbound UI
```

---

## Phase 8 — Count Entry

**Goal:** The core input screen. Works for products (3 fields) and packaging/other (1 field).

### Tasks
- [ ] `app/routes/pages/inventory.py` — `GET /count/{product_id}/{location_id}` (optional `?state=filled|unfilled`)
- [ ] `app/templates/count_entry.html` extends base:
  - [ ] Header: product name + state if applicable
  - [ ] Sub-header: "At [Location Name]"
  - [ ] Last count display (or "No count recorded yet")
  - [ ] **Products:** Cartons / Cases / Units fields (large tap targets, number inputs)
  - [ ] **Product Packaging / Other:** single Qty field + unit label
  - [ ] Conversion display — live "= N total units" (Alpine.js, updates as fields change)
  - [ ] "~ Estimated count" toggle (default off)
  - [ ] Notes field (optional, one line)
  - [ ] **If inbound location:** Carrier selector + Tracking number field
  - [ ] Large full-width Save button (calls `POST /api/inventory/count` via Alpine.js fetch, then redirects)
- [ ] Verify: save creates DB record; redirect returns to Location View; 0 entry hides item

### Commit
```
feat(phase-8): count entry — product 3-field input, packaging single field, save + redirect
```

---

## Phase 9 — Receive Inventory

**Goal:** Distribute an inbound shipment across real locations.

### Tasks
- [ ] `app/routes/pages/inventory.py` — `GET /receive/{inventory_count_id}`
- [ ] `app/templates/receive.html` extends base:
  - [ ] Header: "Receive — [Item Name]" + state if applicable
  - [ ] Inbound summary: qty + carrier + tracking link
  - [ ] "How many did you receive?" — large number field, defaults to inbound qty
  - [ ] Unit selector: Carton / Case / Unit (locked for whole operation)
  - [ ] Distribute section: one row per real location, number input (default 0)
  - [ ] Running tally: "Assigned: X · Remaining: Y" (Alpine.js live)
  - [ ] "Confirm Receipt" button — disabled until assigned = received; calls `POST /api/inventory/receive`
  - [ ] On confirm: redirect to Inbound Location View

### Commit
```
feat(phase-9): receive inventory — distribute inbound, remainder tracking
```

---

## Phase 10 — Products List + Product Detail

**Goal:** Browse all products. See cross-location breakdown for any single item.

### Tasks
- [ ] `app/routes/pages/products.py`:
  - [ ] `GET /products` — renders products list
  - [ ] `GET /products/{id}` — renders product detail
- [ ] `app/templates/products_list.html` extends base:
  - [ ] Search bar (Alpine.js live filter, client-side only)
  - [ ] Products / Product Packaging / Other sections, alphabetical
  - [ ] Tap any item → Product Detail
- [ ] `app/templates/product_detail.html` extends base:
  - [ ] Totals: has_states=False → "Total: N units"; has_states=True → "Filled: N · Unfilled: N"
  - [ ] Per-location breakdown table (non-zero only, `~` for approximate)
  - [ ] History table (most recent 20 entries)

### Commit
```
feat(phase-10): products list + product detail with cross-location totals
```

---

## Phase 11 — Settings: Product Catalog

**Goal:** Add, edit, deactivate products from the Settings screen.

### Tasks
- [ ] `app/routes/pages/settings.py`:
  - [ ] `GET /settings/products` — product catalog list
  - [ ] `GET /settings/products/new` — add form
  - [ ] `GET /settings/products/{id}/edit` — edit form
- [ ] `app/templates/product_catalog.html` extends base:
  - [ ] Search bar
  - [ ] Products / Packaging / Other sections with hierarchy info
  - [ ] "+ New Item" button
  - [ ] Tap existing → edit form
- [ ] `app/templates/product_form.html` extends base (shared add/edit):
  - [ ] Name, Category selector
  - [ ] Conditional fields: has_states toggle → filled/unfilled hierarchy OR single hierarchy
  - [ ] Packaging/Other: unit label field
  - [ ] **New items only:** Initial Inventory section (one row per active location)
  - [ ] Save / Cancel / Delete (with confirmation, soft delete)

### Commit
```
feat(phase-11): settings — product catalog CRUD with initial inventory entry
```

---

## Phase 12 — Settings: Location Management

**Goal:** Add, edit locations from Settings.

### Tasks
- [ ] `app/routes/pages/settings.py`:
  - [ ] `GET /settings/locations` — location list
  - [ ] `GET /settings/locations/new` — add form
  - [ ] `GET /settings/locations/{id}/edit` — edit form
- [ ] `app/templates/location_management.html` extends base:
  - [ ] List: all locations, name + default unit + inbound badge
  - [ ] "+ New Location" button
- [ ] `app/templates/location_form.html` extends base:
  - [ ] Name, Default unit selector, Inbound toggle
  - [ ] Save / Cancel / Delete (warns if inventory counts exist)

### Commit
```
feat(phase-12): settings — location management CRUD
```

---

## Phase 13 — Count History Report

**Goal:** Filterable history log. Low priority — build last.

### Tasks
- [ ] `app/routes/pages/reports.py` — `GET /reports/history`
- [ ] `app/templates/count_history.html` extends base:
  - [ ] Collapsible filters: Item (multi-select), Location (multi-select), Date range (default last 30 days)
  - [ ] History table: Date · Item · Category · Location · State · Qty · Unit · `~` flag
  - [ ] Most recent first

### Commit
```
feat(phase-13): count history report with filters
```

---

## Phase 14 — Mobile Polish + End-to-End Verification

**Goal:** Test the full flow on iPhone (or Safari responsive mode). Fix anything that fails the UX constraints.

### Tasks
- [ ] Test full counting flow: navigate to location → tap item → enter count → save → verify in Location View
- [ ] Test Add Item flow: "+ Add Item" → search → tap → Count Entry → save
- [ ] Test Receive flow: Inbound location → tap Receive → distribute → confirm → verify remainder
- [ ] Test Product Catalog: add new product with initial inventory → verify counts appear
- [ ] Verify all tap targets are large enough (minimum 44px)
- [ ] Verify readable in high-contrast (simulate sunlight)
- [ ] Verify PWA: Safari → Share → Add to Home Screen → opens standalone, no browser chrome
- [ ] Fix any issues found

### Commit
```
chore(phase-14): mobile polish + end-to-end verification pass
```

---

## Phase 15 — Production Deploy

**Goal:** App running on the Ubuntu VM, accessible via Cloudflare Access.

### Tasks
- [ ] Push repo to GitHub (confirm remote exists: `git remote -v`)
- [ ] SSH to prod VM: `ssh jayk1@192.168.0.124`
- [ ] Clone repo to `~/bb-inventory` (or pull if already there)
- [ ] Copy `.env` to VM (manual — never commit)
- [ ] `docker-compose up --build -d`
- [ ] Verify app responds on VM's internal IP
- [ ] Confirm Cloudflare Access is protecting the endpoint (Google SSO, info@boozebaggers.com)

### Commit
```
chore(phase-15): production deploy — app live on Ubuntu VM
```

---

## Status Tracking

Update this table as phases complete. Use commit hash from `git log --oneline`.

| Phase | Name | Status | Commit |
|---|---|---|---|
| Git Setup | Init repo | pending | — |
| 0 | Scaffolding | pending | — |
| 1 | Data Models | pending | — |
| 2 | Seed Data | pending | — |
| 3 | Service Layer | pending | — |
| 4 | REST API Routes | pending | — |
| 5 | Base Template + PWA | pending | — |
| 6 | Dashboard | pending | — |
| 7 | Location View | pending | — |
| 8 | Count Entry | pending | — |
| 9 | Receive Inventory | pending | — |
| 10 | Products List + Detail | pending | — |
| 11 | Settings: Product Catalog | pending | — |
| 12 | Settings: Location Mgmt | pending | — |
| 13 | Count History Report | pending | — |
| 14 | Mobile Polish | pending | — |
| 15 | Production Deploy | pending | — |

---

## Notes

- **Port:** Using 8001 locally (not 8000 — that's occupied by timecard-app)
- **DB:** SQLite in `./data/inventory.db` (Docker volume); gitignored
- **Auth:** Zero auth in-app. Cloudflare Access handles it entirely — do not add any.
- **Resume protocol:** `git log --oneline` → find last phase commit → pick up at next unchecked phase
