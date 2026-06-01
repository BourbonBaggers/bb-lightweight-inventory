from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.locations import get_all_locations
from app.services.products import get_all_products

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/reports/history", response_class=HTMLResponse)
def count_history(
    request: Request,
    db: Session = Depends(get_db),
    product_id: int | None = Query(None),
    location_id: int | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
):
    from app.models import InventoryCount

    q = db.query(InventoryCount).order_by(InventoryCount.counted_at.desc())

    if product_id:
        q = q.filter(InventoryCount.product_id == product_id)
    if location_id:
        q = q.filter(InventoryCount.location_id == location_id)

    if date_from:
        try:
            q = q.filter(InventoryCount.counted_at >= datetime.fromisoformat(date_from))
        except ValueError:
            pass
    else:
        default_from = datetime.now(timezone.utc) - timedelta(days=30)
        q = q.filter(InventoryCount.counted_at >= default_from)

    if date_to:
        try:
            q = q.filter(InventoryCount.counted_at <= datetime.fromisoformat(date_to))
        except ValueError:
            pass

    counts = q.limit(200).all()

    rows = []
    for c in counts:
        rows.append({
            "counted_at": c.counted_at,
            "product_name": c.product.name,
            "category": c.product.category.value,
            "location_name": c.location.name,
            "state": c.state.value if c.state else None,
            "cartons_qty": c.cartons_qty or 0,
            "cases_qty": c.cases_qty or 0,
            "units_qty": c.units_qty or 0,
            "unit_label": c.product.packaging_unit_label or "units",
            "is_approximate": c.is_approximate,
        })

    return templates.TemplateResponse("count_history.html", {
        "request": request,
        "active_page": "history",
        "nav_locations": get_all_locations(db),
        "rows": rows,
        "all_products": get_all_products(db),
        "all_locations": get_all_locations(db),
        "filter_product_id": product_id,
        "filter_location_id": location_id,
        "filter_date_from": date_from or (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d"),
        "filter_date_to": date_to or "",
    })
