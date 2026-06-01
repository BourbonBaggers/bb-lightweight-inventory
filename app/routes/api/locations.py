from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import locations as svc

router = APIRouter(prefix="/api/locations", tags=["locations"])


@router.get("")
def list_locations(db: Session = Depends(get_db)):
    locs = svc.get_all_locations(db)
    return [
        {
            "id": l.id,
            "name": l.name,
            "default_unit": l.default_unit,
            "is_inbound": l.is_inbound,
        }
        for l in locs
    ]


@router.post("", status_code=201)
def create_location(data: dict, db: Session = Depends(get_db)):
    loc = svc.create_location(db, data)
    return {"id": loc.id, "name": loc.name, "default_unit": loc.default_unit, "is_inbound": loc.is_inbound}


@router.put("/{location_id}")
def update_location(location_id: int, data: dict, db: Session = Depends(get_db)):
    loc = svc.update_location(db, location_id, data)
    return {"id": loc.id, "name": loc.name, "default_unit": loc.default_unit, "is_inbound": loc.is_inbound}


@router.delete("/{location_id}", status_code=204)
def delete_location(location_id: int, db: Session = Depends(get_db)):
    svc.delete_location(db, location_id)
