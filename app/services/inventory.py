from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import InventoryCount, Product, Location, State


def current_count(
    db: Session, product_id: int, location_id: int, state: State | None
) -> InventoryCount | None:
    q = (
        db.query(InventoryCount)
        .filter(
            InventoryCount.product_id == product_id,
            InventoryCount.location_id == location_id,
            InventoryCount.state == state,
        )
        .order_by(InventoryCount.counted_at.desc())
    )
    return q.first()


def current_counts_for_location(db: Session, location_id: int) -> list[InventoryCount]:
    """Latest non-zero count per (product, state) combination at this location."""
    from sqlalchemy import func

    subq = (
        db.query(
            InventoryCount.product_id,
            InventoryCount.state,
            func.max(InventoryCount.counted_at).label("max_at"),
        )
        .filter(InventoryCount.location_id == location_id)
        .group_by(InventoryCount.product_id, InventoryCount.state)
        .subquery()
    )

    counts = (
        db.query(InventoryCount)
        .join(
            subq,
            (InventoryCount.product_id == subq.c.product_id)
            & (func.coalesce(InventoryCount.state, '') == func.coalesce(subq.c.state, ''))
            & (InventoryCount.counted_at == subq.c.max_at)
            & (InventoryCount.location_id == location_id),
        )
        .all()
    )

    return [c for c in counts if _total_units(c) > 0]


def current_counts_for_product(db: Session, product_id: int) -> list[InventoryCount]:
    """Latest non-zero count per (location, state) combination for this product."""
    from sqlalchemy import func

    subq = (
        db.query(
            InventoryCount.location_id,
            InventoryCount.state,
            func.max(InventoryCount.counted_at).label("max_at"),
        )
        .filter(InventoryCount.product_id == product_id)
        .group_by(InventoryCount.location_id, InventoryCount.state)
        .subquery()
    )

    counts = (
        db.query(InventoryCount)
        .join(
            subq,
            (InventoryCount.location_id == subq.c.location_id)
            & (func.coalesce(InventoryCount.state, '') == func.coalesce(subq.c.state, ''))
            & (InventoryCount.counted_at == subq.c.max_at)
            & (InventoryCount.product_id == product_id),
        )
        .all()
    )

    return [c for c in counts if _total_units(c) > 0]


def _total_units(count: InventoryCount) -> int:
    cpc = count.cpc_snapshot or 0
    upc = count.upc_snapshot or 0
    cartons = count.cartons_qty or 0
    cases = count.cases_qty or 0
    units = count.units_qty or 0
    if cpc and upc:
        return (cartons * cpc * upc) + (cases * upc) + units
    return units


def total_units(count: InventoryCount) -> int:
    return _total_units(count)


def save_count(
    db: Session,
    product_id: int,
    location_id: int,
    state: State | None = None,
    cartons_qty: int = 0,
    cases_qty: int = 0,
    units_qty: int = 0,
    is_approximate: bool = False,
    notes: str | None = None,
    carrier: str | None = None,
    tracking_number: str | None = None,
    counted_at: datetime | None = None,
) -> InventoryCount:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if state == State.filled:
        cpc = product.filled_cases_per_carton
        upc = product.filled_units_per_case
    elif state == State.unfilled:
        cpc = product.unfilled_cases_per_carton
        upc = product.unfilled_units_per_case
    else:
        cpc = product.cases_per_carton
        upc = product.units_per_case

    record = InventoryCount(
        product_id=product_id,
        location_id=location_id,
        state=state,
        cartons_qty=cartons_qty,
        cases_qty=cases_qty,
        units_qty=units_qty,
        is_approximate=is_approximate,
        notes=notes,
        carrier=carrier,
        tracking_number=tracking_number,
        cpc_snapshot=cpc,
        upc_snapshot=upc,
        counted_at=counted_at or datetime.now(timezone.utc),
    )
    db.add(record)
    return record


def items_not_at_location(db: Session, location_id: int) -> list[Product]:
    """Active products that have no current (non-zero) count at this location."""
    present_ids = {c.product_id for c in current_counts_for_location(db, location_id)}
    all_active = db.query(Product).filter(Product.is_active == True).order_by(Product.name).all()  # noqa: E712
    return [p for p in all_active if p.id not in present_ids]


def history_for_product(
    db: Session, product_id: int, limit: int = 20
) -> list[InventoryCount]:
    return (
        db.query(InventoryCount)
        .filter(InventoryCount.product_id == product_id)
        .order_by(InventoryCount.counted_at.desc())
        .limit(limit)
        .all()
    )


def receive_inbound(
    db: Session,
    inbound_count_id: int,
    received_qty: int,
    received_unit: str,
    distribution: dict[int, int],
) -> None:
    """
    Distribute a received shipment to real locations and update the inbound remainder.
    distribution: {location_id: qty}
    received_unit: 'carton' | 'case' | 'unit'
    """
    inbound = db.query(InventoryCount).filter(InventoryCount.id == inbound_count_id).first()
    if not inbound:
        raise HTTPException(status_code=404, detail="Inbound count not found")

    assigned = sum(distribution.values())
    if assigned != received_qty:
        raise HTTPException(
            status_code=400,
            detail=f"Distribution total ({assigned}) must equal received quantity ({received_qty})",
        )

    for loc_id, qty in distribution.items():
        if qty <= 0:
            continue
        existing = current_count(db, inbound.product_id, loc_id, inbound.state)
        base_cartons = existing.cartons_qty or 0 if existing else 0
        base_cases = existing.cases_qty or 0 if existing else 0
        base_units = existing.units_qty or 0 if existing else 0

        new_cartons = base_cartons + (qty if received_unit == "carton" else 0)
        new_cases = base_cases + (qty if received_unit == "case" else 0)
        new_units = base_units + (qty if received_unit == "unit" else 0)

        save_count(
            db,
            product_id=inbound.product_id,
            location_id=loc_id,
            state=inbound.state,
            cartons_qty=new_cartons,
            cases_qty=new_cases,
            units_qty=new_units,
        )

    inbound_original = (
        (inbound.cartons_qty or 0) if received_unit == "carton"
        else (inbound.cases_qty or 0) if received_unit == "case"
        else (inbound.units_qty or 0)
    )
    remainder = inbound_original - received_qty

    remainder_cartons = max(0, (inbound.cartons_qty or 0) - (received_qty if received_unit == "carton" else 0))
    remainder_cases = max(0, (inbound.cases_qty or 0) - (received_qty if received_unit == "case" else 0))
    remainder_units = max(0, (inbound.units_qty or 0) - (received_qty if received_unit == "unit" else 0))

    save_count(
        db,
        product_id=inbound.product_id,
        location_id=inbound.location_id,
        state=inbound.state,
        cartons_qty=remainder_cartons,
        cases_qty=remainder_cases,
        units_qty=remainder_units,
        carrier=inbound.carrier,
        tracking_number=inbound.tracking_number,
    )

    db.commit()
