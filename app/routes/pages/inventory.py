from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import State
from app.services.locations import get_all_locations, get_location
from app.services.products import get_product
from app.services.inventory import current_count

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/count/{product_id}/{location_id}", response_class=HTMLResponse)
def count_entry(
    product_id: int,
    location_id: int,
    request: Request,
    state: str | None = Query(None),
    db: Session = Depends(get_db),
):
    product = get_product(db, product_id)
    location = get_location(db, location_id)
    state_enum = State(state) if state else None

    existing = current_count(db, product_id, location_id, state_enum)

    cpc = upc = None
    if state_enum == State.filled:
        cpc = product.filled_cases_per_carton
        upc = product.filled_units_per_case
    elif state_enum == State.unfilled:
        cpc = product.unfilled_cases_per_carton
        upc = product.unfilled_units_per_case
    else:
        cpc = product.cases_per_carton
        upc = product.units_per_case

    return templates.TemplateResponse("count_entry.html", {
        "request": request,
        "active_location_id": location_id,
        "nav_locations": get_all_locations(db),
        "product": product,
        "location": location,
        "state": state,
        "existing": existing,
        "cpc": cpc,
        "upc": upc,
    })


@router.get("/receive/{count_id}", response_class=HTMLResponse)
def receive_view(count_id: int, request: Request, db: Session = Depends(get_db)):
    from app.models import InventoryCount
    inbound = db.query(InventoryCount).filter(InventoryCount.id == count_id).first()
    if not inbound:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Count not found")

    product = get_product(db, inbound.product_id)
    inbound_location = get_location(db, inbound.location_id)
    all_locations = get_all_locations(db)
    real_locations = [l for l in all_locations if not l.is_inbound]

    return templates.TemplateResponse("receive.html", {
        "request": request,
        "active_location_id": inbound.location_id,
        "nav_locations": all_locations,
        "product": product,
        "inbound": inbound,
        "inbound_location": inbound_location,
        "real_locations": real_locations,
        "state": inbound.state.value if inbound.state else None,
    })
