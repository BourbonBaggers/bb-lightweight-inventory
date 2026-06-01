from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import State
from app.services import inventory as svc

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


def _count_dict(c):
    return {
        "id": c.id,
        "product_id": c.product_id,
        "location_id": c.location_id,
        "state": c.state,
        "cartons_qty": c.cartons_qty,
        "cases_qty": c.cases_qty,
        "units_qty": c.units_qty,
        "counted_at": c.counted_at.isoformat(),
        "is_approximate": c.is_approximate,
        "cpc_snapshot": c.cpc_snapshot,
        "upc_snapshot": c.upc_snapshot,
        "notes": c.notes,
        "carrier": c.carrier,
        "tracking_number": c.tracking_number,
        "total_units": svc.total_units(c),
    }


@router.get("/location/{location_id}")
def counts_for_location(location_id: int, db: Session = Depends(get_db)):
    return [_count_dict(c) for c in svc.current_counts_for_location(db, location_id)]


@router.get("/product/{product_id}")
def counts_for_product(product_id: int, db: Session = Depends(get_db)):
    return [_count_dict(c) for c in svc.current_counts_for_product(db, product_id)]


@router.get("/history/{product_id}")
def history(product_id: int, db: Session = Depends(get_db)):
    return [_count_dict(c) for c in svc.history_for_product(db, product_id)]


@router.get("/not-at-location/{location_id}")
def not_at_location(location_id: int, db: Session = Depends(get_db)):
    return svc.items_not_at_location(db, location_id)


@router.post("/count", status_code=201)
def save_count(data: dict, db: Session = Depends(get_db)):
    state_val = data.pop("state", None)
    state = State(state_val) if state_val else None
    record = svc.save_count(db, state=state, **data)
    db.commit()
    db.refresh(record)
    return _count_dict(record)


@router.post("/receive", status_code=200)
def receive_inbound(data: dict, db: Session = Depends(get_db)):
    svc.receive_inbound(
        db,
        inbound_count_id=data["inbound_count_id"],
        received_qty=data["received_qty"],
        received_unit=data["received_unit"],
        distribution=data["distribution"],
    )
    return {"ok": True}
