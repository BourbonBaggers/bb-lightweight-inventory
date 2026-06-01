from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Location


def get_all_locations(db: Session) -> list[Location]:
    return db.query(Location).order_by(Location.name).all()


def get_location(db: Session, location_id: int) -> Location:
    loc = db.query(Location).filter(Location.id == location_id).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")
    return loc


def create_location(db: Session, data: dict) -> Location:
    loc = Location(**data)
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return loc


def update_location(db: Session, location_id: int, data: dict) -> Location:
    loc = get_location(db, location_id)
    for key, value in data.items():
        setattr(loc, key, value)
    db.commit()
    db.refresh(loc)
    return loc


def delete_location(db: Session, location_id: int) -> None:
    from app.models import InventoryCount
    loc = get_location(db, location_id)
    has_counts = db.query(InventoryCount).filter(
        InventoryCount.location_id == location_id
    ).first()
    if has_counts:
        raise HTTPException(
            status_code=409,
            detail="Location has inventory records — remove all counts before deleting",
        )
    db.delete(loc)
    db.commit()
