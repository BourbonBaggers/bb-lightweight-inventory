from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import products as svc


router = APIRouter(prefix="/api/products", tags=["products"])


def _product_dict(p):
    return {
        "id": p.id,
        "name": p.name,
        "category": p.category,
        "has_states": p.has_states,
        "cases_per_carton": p.cases_per_carton,
        "units_per_case": p.units_per_case,
        "filled_cases_per_carton": p.filled_cases_per_carton,
        "filled_units_per_case": p.filled_units_per_case,
        "unfilled_cases_per_carton": p.unfilled_cases_per_carton,
        "unfilled_units_per_case": p.unfilled_units_per_case,
        "packaging_unit_label": p.packaging_unit_label,
        "is_active": p.is_active,
    }


@router.get("")
def list_products(active: bool = Query(True), db: Session = Depends(get_db)):
    return [_product_dict(p) for p in svc.get_all_products(db, active_only=active)]


@router.post("", status_code=201)
def create_product(data: dict, db: Session = Depends(get_db)):
    return _product_dict(svc.create_product(db, data))


@router.put("/{product_id}")
def update_product(product_id: int, data: dict, db: Session = Depends(get_db)):
    return _product_dict(svc.update_product(db, product_id, data))


@router.delete("/{product_id}", status_code=204)
def deactivate_product(product_id: int, db: Session = Depends(get_db)):
    svc.deactivate_product(db, product_id)
