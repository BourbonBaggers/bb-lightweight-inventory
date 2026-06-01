# BB Lightweight Inventory — Product Requirements

## PWA Requirement
The app must be installable as a Progressive Web App (PWA) on iPhone. This means:
- A `manifest.json` with app name, icon, theme color, and `display: standalone`
- A minimal service worker (install only — no offline caching needed)
- `<meta name="apple-mobile-web-app-capable">` tags in the base template

When added to the iPhone home screen via Safari → Share → Add to Home Screen, the app opens
full-screen with no browser chrome. This is the expected primary usage pattern.

---

## What This Is
A simple internal inventory quantity tracker for Bourbon Baggers (solopreneur — Jay + wife).
Tracks product and packaging counts across physical locations so you know what you have and
where, primarily to know when to reorder.

**Primary use mode:** Standing at a location on an iPhone, counting items visually, entering
or reviewing quantities. Updates happen roughly once per week per location. Nothing is urgent,
nothing is high-volume.

**Secondary use mode:** Sitting on the couch, checking totals across locations out of curiosity
or to plan an order.

---

## What This Is Not
These are explicitly out of scope — do not suggest, add, or build any of these:
- Cost or value tracking of any kind
- COGS or accounting
- Purchase history or order integration
- Automatic reorder alerts or notifications
- Barcode scanning (initial scope — revisit only if explicitly requested)
- In-app authentication (Cloudflare Access handles auth entirely)
- Offline mode or sync
- Kit/bundle explosion or BOM tracking
- Reporting dashboards or data exports

---

## Data Model

### Location
| Field | Type | Notes |
|---|---|---|
| id | int | primary key |
| name | string | e.g., "Storage Unit", "Garage", "Trailer", "Office", "Inbound" |
| default_unit | enum | `carton` / `case` / `unit` — suggested default when entering a count |
| is_inbound | boolean | when true, count entry shows carrier + tracking number fields (default false) |

Locations are not hardcoded. Managed through Settings. Current locations: Storage Unit (carton
default), Garage (case default), Trailer (unit default), Office (unit default), Inbound (unit
default, is_inbound = true).

**Inbound location** represents items on order / in transit from a supplier. Applies to
packaging materials and finished goods (e.g., glasses) arriving from Chinese or US suppliers.
When an item arrives and is physically received, count it at the real destination location and
set its Inbound count to 0.

---

### Product
| Field | Type | Notes |
|---|---|---|
| id | int | primary key |
| name | string | display name, e.g., "Founders Flight" |
| category | enum | `product` / `product_packaging` / `other` |
| has_states | boolean | whether this item can be filled (ready for sale) vs unfilled (needs assembly) |
| cases_per_carton | int | nullable — products with `has_states = false` only |
| units_per_case | int | nullable — products with `has_states = false` only |
| filled_cases_per_carton | int | nullable — products with `has_states = true`, filled state |
| filled_units_per_case | int | nullable — products with `has_states = true`, filled state |
| unfilled_cases_per_carton | int | nullable — products with `has_states = true`, unfilled state |
| unfilled_units_per_case | int | nullable — products with `has_states = true`, unfilled state |
| packaging_unit_label | string | nullable — product_packaging and other only (e.g., "bag", "bundle") |
| is_active | boolean | soft delete — hide from active lists without losing history |

**Category: `product`** — sellable finished goods with a carton→case→unit hierarchy.
**Category: `components`** — ingredients and materials that go into making products: shredded
oak, teabags, sugar, potassium sorbate, tuck boxes, rigid setup boxes, etc. No hierarchy.
Counted in their own natural unit (bag, bundle, box, roll, etc.).
**Category: `shipping`** — outbound shipping supplies: cardboard shipping boxes, mailers, etc.
No hierarchy. Counted in natural unit.
**Category: `other`** — operational supplies with no direct product relationship: sampling
bourbon, handle sacks, tape, labels, bags, etc. No hierarchy. Counted in natural unit.

Categories are fixed in code (not user-configurable). Four is the right number for this
business — adding a dynamic category system would add complexity with no benefit.

`has_states` applies to products that exist in two states at the same location simultaneously:
- `unfilled` — assembled packaging, not yet stuffed/finished (needs assembly)
- `filled` — finished, ready for sale

Example: Founders Flight can be "10 unfilled cartons" and "2 filled cartons" at the same
location at the same time. Most products will have `has_states = false` and just have one count.

---

### InventoryCount
| Field | Type | Notes |
|---|---|---|
| id | int | primary key |
| product_id | int | foreign key → Product |
| location_id | int | foreign key → Location |
| state | enum | `filled` / `unfilled` / null — null if `product.has_states = false` |
| cartons_qty | int | nullable — products only, carton-level count (default 0) |
| cases_qty | int | nullable — products only, case-level count (default 0) |
| units_qty | int | for products: unit-level count (default 0); for product_packaging / other: the single count field |
| counted_at | datetime | timestamp of entry, defaults to now |
| is_approximate | boolean | `false` = exact count, `true` = estimated count — defaults to false |
| cpc_snapshot | int | nullable — cases_per_carton copied from Product at save time (products only) |
| upc_snapshot | int | nullable — units_per_case copied from Product at save time (products only) |
| notes | string | nullable — optional free-text note on this specific count entry |
| carrier | string | nullable — UPS / FedEx / USPS / DHL / Other — only used for inbound locations |
| tracking_number | string | nullable — only used for inbound locations |

**Records are never updated — only inserted.** Current count for a
(product, location, state) combination = the most recent record for that combination.
All prior records = history.

---

## Business Rules

### Units and Conversion
Each InventoryCount stores up to three separate quantities. Total units for a record:

```
total_units = (cartons_qty × cpc × upc) + (cases_qty × upc) + units_qty
```

`cpc` and `upc` are always read from the **snapshot fields on InventoryCount** (`cpc_snapshot`,
`upc_snapshot`), not from the Product. This means historical totals remain accurate even if
the product's hierarchy is changed later (e.g., supplier switches from 6-case to 12-case
cartons). At save time, the correct hierarchy values are copied onto the record.

For the live conversion display in Count Entry: use the Product's current hierarchy values
(since the record hasn't been saved yet).

Product Packaging and Other items use only `units_qty` — no conversion, no snapshots needed.

### What "Current" Means
For any (product, location, state) combination:
- Current count = the most recent `InventoryCount` record ordered by `counted_at DESC`
- A current count of 0 means the item is not present at that location (hidden from view)
- History = all records for that combination, ordered by `counted_at DESC`

### Zeros and Presence
- Items with a current count of 0 are hidden from all location views
- To add an item to a location: create a new count > 0
- To remove an item from a location: enter 0 (saves a new record with quantity 0, hides it)
- The "Add Item" flow at a location shows all products/packaging not currently present there

### Cross-Location Totals
- All current counts for a product are normalized to units for the total
- Displayed both as a single total and as a per-location breakdown
- Packaging totals are shown in their natural unit (no conversion to units)

### Receive + Existing Count Merge
When a receive operation adds quantity to a location that already has a count, the resulting
InventoryCount record carries forward all three fields from the existing record, adding only
the received unit:

```
new_cartons_qty = existing_cartons_qty + received_cartons  (if received in cartons)
new_cases_qty   = existing_cases_qty   (unchanged)
new_units_qty   = existing_units_qty   (unchanged)
```

Same logic applies if receiving in cases or units — only that field increments, the others
carry forward. If the addition looks wrong, the user corrects it via normal Count Entry.
No special error handling or reconciliation UI needed.

---

### Receiving Inbound Inventory
When a shipment arrives, the user counts what they physically have and distributes it across
real locations. The received quantity may be less than the inbound quantity (short shipment).

- **Received quantity** = what actually arrived (entered by user, defaults to inbound quantity)
- **Distribution** = how many go to each real location — must sum to exactly the received quantity
- **Inbound remainder** = inbound quantity − received quantity — stays on inbound automatically
  - If remainder = 0, inbound count goes to 0 (hidden from inbound view)
  - If remainder > 0, the inbound row remains showing the outstanding quantity — no manual step needed
- Receiving creates a new `InventoryCount` record for each destination location (adds to existing count)
- The inbound `InventoryCount` is replaced with the remainder quantity
- Distribution is done in the same unit as the inbound count (e.g., if inbound was in cartons, distribute in cartons)
- State (filled/unfilled) carries through from inbound to all destination locations
- Historical record captures: original inbound qty, received qty, distribution per location, timestamp

---

## App Shell — Sidebar Navigation

The app uses a hamburger + slide-out sidebar as the primary navigation. No long scroll.
Every major section is one or two taps from anywhere in the app.

**Hamburger behavior:**
- Hamburger icon top-left on every screen
- Tap → sidebar slides in from the left
- Tap any nav item → sidebar closes, view loads
- Tap outside sidebar → closes without navigating

**Sidebar structure:**
```
☰  BB Inventory
─────────────────
  Dashboard
─────────────────
  Locations ▾
    Storage Unit
    Garage
    Trailer
    Office
    Inbound
    [any added locations]
─────────────────
  Products ▾
    Products
    (all categories shown in one Products List view)
─────────────────
  Reports ▾
    Count History
    [room for future reports]
─────────────────
  Settings ▾
    Manage Products
    Manage Locations
```

- All ▾ groups are expandable — tap header to collapse/expand
- Tapping a leaf item closes the sidebar and loads that view
- Active item highlighted so you always know where you are

---

## Screens

### 1. Dashboard
Default view when the app opens.

**Layout:**
- Header: "BB Inventory" + hamburger icon
- **Products accordion** (collapsed by default)
  - Header: "Products (X items)" — tap to expand
  - Each product: name + total filled units + total unfilled units (if has_states)
  - Tap any row → Product Detail
- **Product Packaging accordion** (collapsed by default)
  - Header: "Product Packaging (X items)" — tap to expand
  - Each item: name + total quantity in natural unit
  - Tap any row → Product Detail
- **Other accordion** (collapsed by default)
  - Header: "Other (X items)" — tap to expand
  - Each item: name + total quantity in natural unit
  - Tap any row → Product Detail
- **Locations summary** — compact row per location (always visible, no accordion)
  - Location name + count of non-zero items currently there
  - Tap a row → that Location View

---

### 2. Location View
One view per location. Accessed via sidebar — no back button, sidebar is the navigation.

**Layout:**
- Header: location name + hamburger icon
- **"+ Add Item" button** (top right — deliberate management action, not a counting action)
- **Products accordion** (collapsed by default)
  - Header: "Products (X items)" — tap to expand
  - Non-zero items only, alphabetical
  - Products with `has_states = true`: two rows per product — "Filled: X cart / Y case / Z unit" and "Unfilled: X cart / Y case / Z unit"
  - Products with `has_states = false`: one row — "Name: X cart / Y case / Z unit"
  - On inbound locations: carrier + tracking link shown below item name (if present)
  - On inbound locations: each item row shows a **"Receive" button** → Receive Inventory screen
  - Tap item name/row (not Receive button) → Count Entry
- **Product Packaging accordion** (collapsed by default)
  - Header: "Product Packaging (X items)" — tap to expand
  - Non-zero items only, alphabetical
  - One row per item: "Name: X bags" — approximate counts shown as "~X bags"
  - On inbound locations: carrier + tracking link shown below item name (if present)
  - On inbound locations: each item row shows a **"Receive" button** → Receive Inventory screen
  - Tap item name/row (not Receive button) → Count Entry
- **Other accordion** (collapsed by default)
  - Header: "Other (X items)" — tap to expand
  - Same row behavior as Product Packaging
  - On inbound locations: same carrier + tracking + Receive button behavior

**"+ Add Item" flow:**
- Opens a modal sheet listing all active items with current count = 0 at this location
- **Search bar at top** — wildcard/substring match, filters the list live as you type
- Items grouped by category (Products / Product Packaging / Other), alphabetical within groups
- Tap any item → Count Entry (blank, ready for first count)
- **"+ Create new product" row at bottom** — opens the Add/Edit Item form in a new sheet;
  on save, drops directly into Count Entry for that new item at this location (no detour to Settings)

---

### 3. Count Entry
Update the quantity for one item at one location.

**Layout:**
- Header: product name + state if applicable ("Founders Flight — Unfilled") + hamburger icon
- Sub-header: "At [Location Name]"
- Current count display: last recorded values — "Last counted Jun 1, 2026: 3 cartons · 5 cases · 0 units"
  - If never counted here: "No count recorded yet"
- **For products — three labeled input fields** (all visible; leave at 0 to skip):
  - `Cartons  [___]`
  - `Cases    [___]`
  - `Units    [___]`
  - All fields large tap targets — a location can have cartons AND cases AND units simultaneously
- **For product_packaging / other — single quantity field**:
  - `Qty  [___]  [unit label]` (e.g., "Qty ___ bags")
- **Conversion display** (products only, live-updating):
  - "= [N] total units" — sums all three fields using the product's hierarchy for that state
- **"~ Estimated count" toggle** (default off)
  - Saves `is_approximate = true` when on
- **Notes field** (optional, one line, keyboard appears on tap):
  - Placeholder: "e.g., one carton is damaged, mixed old/new batch"
  - Saves to `notes` on the InventoryCount record
- **Inbound fields** — only when `location.is_inbound = true`:
  - Carrier selector: UPS / FedEx / USPS / DHL / Other
  - Tracking number field (large tap target)
- Large **Save** button (full-width, bottom, thumb-reachable)
- On save: inserts InventoryCount with `cartons_qty`, `cases_qty`, `units_qty` populated; returns to Location View

---

### 4. Receive Inventory
Triggered from the "Receive" button on an inbound item row. Handles distributing a
received shipment across real locations, with automatic remainder tracking.

**Layout:**
- Header: "Receive — [Item Name]" + state if applicable + hamburger icon
- **Inbound summary:** "Inbound: 10 cartons · [Carrier] [tracking link]"
- **Quantity Received field** (large, prominent):
  - Label: "How many did you receive?"
  - Defaults to the full inbound quantity
  - Editable — user counts what's actually in hand (handles short shipments)
  - **Unit selector**: Carton / Case / Unit — locked to one unit for the entire receive operation
    (shipments arrive in uniform packaging — not mixed cartons-and-cases in a single receive)
- **Distribute to locations section:**
  - One row per real location (all non-inbound locations listed)
  - Each row: location name + number input (default 0), same unit as Quantity Received
  - Running tally: "Assigned: 6 · Remaining to assign: 4" — counts down as inputs are filled
  - Remaining is based on Quantity Received, not original inbound quantity
- **Confirm button** (full-width, bottom, thumb-reachable)
  - Disabled until assigned total = received quantity
  - Label: "Confirm Receipt"
- On confirm:
  - For each destination location with quantity > 0: adds received quantity to that location's
    current count in the received unit (inserts new InventoryCount = existing + received qty)
  - Updates inbound count to: original inbound − received quantity (in inbound's unit)
  - If remainder = 0, inbound item disappears from Inbound view
  - If remainder > 0, inbound item stays showing the outstanding balance
  - Returns to Inbound Location View
- After receiving, user visually verifies the updated count looks correct and can correct via
  normal Count Entry if needed

---

### 5. Products List
Accessed via sidebar → Products.

**Layout:**
- Header: "Products" + hamburger icon
- **Search bar** — simple wildcard/substring match against item names, filters all three
  sections live as you type; clears with ✕; no indexing, no server round-trip
- Products section (alphabetical) — tap any → Product Detail
- Product Packaging section (alphabetical) — tap any → Product Detail
- Other section (alphabetical) — tap any → Product Detail

---

### 5. Product Detail
Cross-location view for a single product or packaging item.

**Layout:**
- Header: product name + hamburger icon
- **Totals:**
  - `has_states = false`: "Total: 240 units across all locations"
  - `has_states = true`: "Filled: 192 units · Unfilled: 48 units"
- **Per-location breakdown table:**
  - Location / State (if applicable) / Quantity / Unit / Last Counted
  - Non-zero locations only — approximate counts shown with `~` prefix
- **History** (most recent first, last 20 entries):
  - Date · Location · State · Quantity · Unit · "~" if approximate

---

### 6. Settings
Accessed via sidebar → Settings. Low-frequency, intentionally not prominent.

**Layout:**
- Header: "Settings" + hamburger icon
- Manage Products → Product Catalog screen
- Manage Locations → Location Management screen
- (Room for future items)

---

### 6a. Product Catalog

- **Search bar** — wildcard/substring match, filters all categories live as you type
- List: Products first, Product Packaging second, Other third — alphabetical within groups
  - Products: name + hierarchy ("6 cases/carton · 8 units/case")
  - Product Packaging + Other: name + unit label
- **"+ New Item"** button
- Tap existing → Edit Item form

**Add / Edit Item Form:**
- Name
- Category: Product / Product Packaging / Other
- *If Product, `has_states = false`:* Cases per carton · Units per case
- *If Product, `has_states = true`:*
  - Unfilled: Cases per carton · Units per case
  - Filled: Cases per carton · Units per case (enter separately — may differ from unfilled)
- *If Product Packaging or Other:* Unit label (bag / bundle / roll / box / bottle / etc.)
- **Initial Inventory** (optional section — new items only, not shown when editing):
  - One row per location (all active locations listed)
  - *If Product with has_states:* two sub-rows per location (Filled / Unfilled), each with
    quantity input + unit selector
  - *If Product without has_states:* one row per location with quantity input + unit selector
  - *If Product Packaging or Other:* one row per location with quantity input (unit locked to
    item's unit label)
  - Leave any location blank to skip it — blank rows create no inventory record
  - On save: item is created AND one `InventoryCount` record is inserted per non-blank location
- Save · Cancel · Delete (confirmation required; soft delete via `is_active = false`)

---

### 6c. Location Management

- List: all locations with name + default unit + inbound badge if `is_inbound = true`
- **"+ New Location"** button
- Tap existing → Edit Location form

**Add / Edit Location Form:**
- Name
- Default counting unit: Carton / Case / Unit
- Inbound location toggle
- Save · Cancel · Delete (warns if inventory counts exist for this location)

---

### 7. Reports
Accessed via sidebar → Reports (expandable group). Parallel to Settings — its own top-level
section, not buried under configuration.

---

### 7a. Count History Report
Low priority. Build only after core counting and receiving flows are complete and stable.

**Layout:**
- Header: "Count History" + hamburger icon
- **Filters** (collapsible, collapsed by default):
  - Item (multi-select or "All")
  - Location (multi-select or "All")
  - Date range (from / to, defaults to last 30 days)
- **History table** (most recent first):
  - Date · Item · Category · Location · State · Quantity · Unit · "~" if approximate
- **Chart** (very low priority — do not build in initial scope):
  - Quantity over time per item, filterable by location
  - Only meaningful once several months of data exist

---

## Navigation Map

```
App opens → Dashboard
Sidebar → Dashboard
Sidebar → Locations ▾
  → [Location name] → Location View
      → Tap item row → Count Entry → back to Location View
      → Tap "+ Add Item" → modal sheet → Count Entry → back to Location View
      → Tap "Receive" (inbound only) → Receive Inventory → back to Inbound Location View
Sidebar → Products → Products List → Product Detail
Sidebar → Reports ▾
  → Count History → Count History Report
Sidebar → Settings
  → Manage Products → Product Catalog → Add/Edit Item form (includes Initial Inventory)
  → Manage Locations → Location Management → Add/Edit Location form
Dashboard → tap item row → Product Detail
Dashboard → tap location row → Location View
```

---

## API Design Principles

The UI is a client of the API — it does not bypass it. This makes the system agent-ready from day one.

- Every inventory mutation (update count, add product, add location, etc.) is a discrete REST
  endpoint returning JSON
- Business logic lives in service functions (`app/services/`), not in route handlers or templates
- Templates are display-only — no logic, no computation, just rendering
- FastAPI auto-generates an OpenAPI spec at `/docs` — this is the interface an LLM agent will
  eventually use to understand what the system can do
- Route handlers are thin: validate input → call service → return response

When the voice/LLM layer is added, the agent calls the same endpoints the UI already uses.
No new backend needed.

---

## Future Scope (Do Not Build Yet)
- **Voice / LLM inventory entry:** microphone button → speech-to-text → LLM parses the
  description → calls existing REST API endpoints to update counts. The API-first architecture
  means this layer drops in without any backend changes.
- **Barcode scanning** via iPhone camera for product lookup
- **Manual item ordering** in Products List and Location View — user-defined sort order instead
  of alphabetical. Note for implementation: add a `sort_order` integer field to Product when
  building this; don't rework the whole list UI.
- **Empty state / first-run polish** — when no products or inventory exist yet, show a prompt
  rather than a blank dashboard. Low priority since there's only one user who won't be confused.
- **Data backup strategy** — SQLite lives in a Docker volume. A `scripts/backup.sh` that copies
  the `.db` file to a dated backup (locally or rsync'd to the Mac) should be created and
  documented. Broader backup strategy for all internal apps is a separate personal project to
  define. For now: manual backup before any destructive operation.
