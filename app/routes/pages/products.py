from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.locations import get_all_locations
from app.services.products import get_all_products, get_product
from app.services.inventory import (
    current_counts_for_product, history_for_product, total_units
)
from app.models import Category, State

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/products", response_class=HTMLResponse)
def products_list(request: Request, db: Session = Depends(get_db)):
    all_products = get_all_products(db)
    products = [p for p in all_products if p.category == Category.product]
    packaging = [p for p in all_products if p.category == Category.product_packaging]
    other = [p for p in all_products if p.category == Category.other]
    return templates.TemplateResponse("products_list.html", {
        "request": request,
        "active_page": "products",
        "nav_locations": get_all_locations(db),
        "products": products,
        "packaging": packaging,
        "other": other,
    })


@router.get("/products/{product_id}", response_class=HTMLResponse)
def product_detail(product_id: int, request: Request, db: Session = Depends(get_db)):
    product = get_product(db, product_id)
    counts = current_counts_for_product(db, product_id)
    history = history_for_product(db, product_id, limit=20)

    total_filled = total_unfilled = total_all = 0
    location_rows = []

    for c in counts:
        tu = total_units(c)
        row = {
            "location": c.location.name,
            "state": c.state.value if c.state else None,
            "cartons_qty": c.cartons_qty or 0,
            "cases_qty": c.cases_qty or 0,
            "units_qty": c.units_qty or 0,
            "unit_label": product.packaging_unit_label or "units",
            "total_units": tu,
            "is_approximate": c.is_approximate,
            "counted_at": c.counted_at,
        }
        location_rows.append(row)
        if c.state and c.state.value == "filled":
            total_filled += tu
        elif c.state and c.state.value == "unfilled":
            total_unfilled += tu
        else:
            total_all += tu

    history_rows = []
    for c in history:
        history_rows.append({
            "counted_at": c.counted_at,
            "location": c.location.name,
            "state": c.state.value if c.state else None,
            "cartons_qty": c.cartons_qty or 0,
            "cases_qty": c.cases_qty or 0,
            "units_qty": c.units_qty or 0,
            "unit_label": product.packaging_unit_label or "units",
            "is_approximate": c.is_approximate,
        })

    return templates.TemplateResponse("product_detail.html", {
        "request": request,
        "active_page": "products",
        "nav_locations": get_all_locations(db),
        "product": product,
        "total_filled": total_filled,
        "total_unfilled": total_unfilled,
        "total_all": total_all,
        "location_rows": location_rows,
        "history_rows": history_rows,
    })
