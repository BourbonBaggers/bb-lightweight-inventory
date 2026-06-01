from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.locations import get_all_locations, get_location
from app.services.products import get_all_products, get_product

router = APIRouter(prefix="/settings")
templates = Jinja2Templates(directory="app/templates")


# ── Product Catalog ──────────────────────────────────────────────────────────

@router.get("/products", response_class=HTMLResponse)
def product_catalog(request: Request, db: Session = Depends(get_db)):
    all_products = get_all_products(db, active_only=False)
    from app.models import Category
    return templates.TemplateResponse("product_catalog.html", {
        "request": request,
        "active_page": "product_catalog",
        "nav_locations": get_all_locations(db),
        "products": [p for p in all_products if p.category == Category.product],
        "components": [p for p in all_products if p.category == Category.components],
        "shipping": [p for p in all_products if p.category == Category.shipping],
        "other": [p for p in all_products if p.category == Category.other],
    })


@router.get("/products/new", response_class=HTMLResponse)
def new_product_form(
    request: Request,
    location_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    return templates.TemplateResponse("product_form.html", {
        "request": request,
        "active_page": "product_catalog",
        "nav_locations": get_all_locations(db),
        "product": None,
        "locations": get_all_locations(db),
        "return_location_id": location_id,
    })


@router.get("/products/{product_id}/edit", response_class=HTMLResponse)
def edit_product_form(product_id: int, request: Request, db: Session = Depends(get_db)):
    product = get_product(db, product_id)
    return templates.TemplateResponse("product_form.html", {
        "request": request,
        "active_page": "product_catalog",
        "nav_locations": get_all_locations(db),
        "product": product,
        "locations": get_all_locations(db),
        "return_location_id": None,
    })


# ── Location Management ──────────────────────────────────────────────────────

@router.get("/locations", response_class=HTMLResponse)
def location_management(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("location_management.html", {
        "request": request,
        "active_page": "location_mgmt",
        "nav_locations": get_all_locations(db),
        "locations": get_all_locations(db),
    })


@router.get("/locations/new", response_class=HTMLResponse)
def new_location_form(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("location_form.html", {
        "request": request,
        "active_page": "location_mgmt",
        "nav_locations": get_all_locations(db),
        "location": None,
    })


@router.get("/locations/{location_id}/edit", response_class=HTMLResponse)
def edit_location_form(location_id: int, request: Request, db: Session = Depends(get_db)):
    location = get_location(db, location_id)
    return templates.TemplateResponse("location_form.html", {
        "request": request,
        "active_page": "location_mgmt",
        "nav_locations": get_all_locations(db),
        "location": location,
    })
