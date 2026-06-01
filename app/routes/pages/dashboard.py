from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Category
from app.services.products import get_all_products
from app.services.inventory import current_counts_for_product, total_units
from app.services.locations import get_all_locations

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    locations = get_all_locations(db)
    products = get_all_products(db)

    products_data = []
    packaging_data = []
    other_data = []

    for p in products:
        counts = current_counts_for_product(db, p.id)
        if not counts:
            continue

        if p.has_states:
            filled = sum(total_units(c) for c in counts if c.state and c.state.value == "filled")
            unfilled = sum(total_units(c) for c in counts if c.state and c.state.value == "unfilled")
            total = filled + unfilled
        else:
            total = sum(total_units(c) for c in counts)
            filled = unfilled = None

        item = {
            "id": p.id,
            "name": p.name,
            "has_states": p.has_states,
            "total": total,
            "filled": filled,
            "unfilled": unfilled,
            "unit_label": p.packaging_unit_label or "units",
        }

        if p.category == Category.product:
            products_data.append(item)
        elif p.category == Category.product_packaging:
            packaging_data.append(item)
        else:
            other_data.append(item)

    location_summaries = []
    for loc in locations:
        from app.services.inventory import current_counts_for_location
        loc_counts = current_counts_for_location(db, loc.id)
        unique_items = len({c.product_id for c in loc_counts})
        location_summaries.append({"id": loc.id, "name": loc.name, "item_count": unique_items})

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "active_page": "dashboard",
        "nav_locations": locations,
        "products_data": products_data,
        "packaging_data": packaging_data,
        "other_data": other_data,
        "location_summaries": location_summaries,
    })
