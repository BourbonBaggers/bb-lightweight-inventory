from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Product


def get_all_products(db: Session, active_only: bool = True) -> list[Product]:
    q = db.query(Product)
    if active_only:
        q = q.filter(Product.is_active == True)  # noqa: E712
    return q.order_by(Product.name).all()


def get_product(db: Session, product_id: int) -> Product:
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    return p


def create_product(db: Session, data: dict) -> Product:
    inventory_entries = data.pop("initial_inventory", None)
    product = Product(**data)
    db.add(product)
    db.flush()

    if inventory_entries:
        from app.services.inventory import save_count
        for entry in inventory_entries:
            if entry.get("units_qty", 0) or entry.get("cases_qty", 0) or entry.get("cartons_qty", 0):
                save_count(db, product_id=product.id, **entry)

    db.commit()
    db.refresh(product)
    return product


def update_product(db: Session, product_id: int, data: dict) -> Product:
    product = get_product(db, product_id)
    for key, value in data.items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product


def deactivate_product(db: Session, product_id: int) -> Product:
    product = get_product(db, product_id)
    product.is_active = False
    db.commit()
    db.refresh(product)
    return product
