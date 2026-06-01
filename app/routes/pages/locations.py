from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Category, State
from app.services.locations import get_all_locations, get_location
from app.services.inventory import current_counts_for_location, items_not_at_location

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _build_location_context(db: Session, location_id: int) -> dict:
    location = get_location(db, location_id)
    all_locations = get_all_locations(db)
    counts = current_counts_for_location(db, location_id)

    products = []
    packaging = []
    other = []

    for c in counts:
        p = c.product
        entry = {
            "count_id": c.id,
            "product_id": p.id,
            "name": p.name,
            "state": c.state.value if c.state else None,
            "cartons_qty": c.cartons_qty or 0,
            "cases_qty": c.cases_qty or 0,
            "units_qty": c.units_qty or 0,
            "is_approximate": c.is_approximate,
            "carrier": c.carrier,
            "tracking_number": c.tracking_number,
            "has_states": p.has_states,
            "unit_label": p.packaging_unit_label or "units",
        }
        if p.category == Category.product:
            products.append(entry)
        elif p.category == Category.product_packaging:
            packaging.append(entry)
        else:
            other.append(entry)

    products.sort(key=lambda x: x["name"])
    packaging.sort(key=lambda x: x["name"])
    other.sort(key=lambda x: x["name"])

    not_here = items_not_at_location(db, location_id)
    add_items = [
        {
            "id": p.id,
            "name": p.name,
            "category": p.category.value,
            "has_states": p.has_states,
        }
        for p in not_here
    ]

    return {
        "location": location,
        "nav_locations": all_locations,
        "active_location_id": location_id,
        "products": products,
        "packaging": packaging,
        "other": other,
        "add_items": add_items,
    }


@router.get("/locations/{location_id}", response_class=HTMLResponse)
def location_view(location_id: int, request: Request, db: Session = Depends(get_db)):
    ctx = _build_location_context(db, location_id)
    return templates.TemplateResponse("location.html", {"request": request, **ctx})
