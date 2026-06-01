"""
Idempotent seed script. Run inside the container:
  docker-compose exec app python scripts/seed.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import Location, Product, DefaultUnit, Category


LOCATIONS = [
    {"name": "Storage Unit", "default_unit": DefaultUnit.carton, "is_inbound": False},
    {"name": "Garage",       "default_unit": DefaultUnit.case,   "is_inbound": False},
    {"name": "Trailer",      "default_unit": DefaultUnit.unit,   "is_inbound": False},
    {"name": "Office",       "default_unit": DefaultUnit.unit,   "is_inbound": False},
    {"name": "Inbound",      "default_unit": DefaultUnit.unit,   "is_inbound": True},
]

PRODUCTS = [
    {
        "name": "Founders Flight",
        "category": Category.product,
        "has_states": True,
        "filled_cases_per_carton": 6,
        "filled_units_per_case": 4,
        "unfilled_cases_per_carton": 6,
        "unfilled_units_per_case": 4,
    },
    {
        "name": "Single Barrel",
        "category": Category.product,
        "has_states": False,
        "cases_per_carton": 6,
        "units_per_case": 6,
    },
    {
        "name": "Tuck Boxes",
        "category": Category.product_packaging,
        "has_states": False,
        "packaging_unit_label": "box",
    },
    {
        "name": "Oak Chips",
        "category": Category.product_packaging,
        "has_states": False,
        "packaging_unit_label": "bag",
    },
    {
        "name": "Handle Sacks",
        "category": Category.other,
        "has_states": False,
        "packaging_unit_label": "bundle",
    },
]


def seed():
    db = SessionLocal()
    try:
        existing_locations = {loc.name for loc in db.query(Location).all()}
        for loc_data in LOCATIONS:
            if loc_data["name"] not in existing_locations:
                db.add(Location(**loc_data))
                print(f"  + Location: {loc_data['name']}")
            else:
                print(f"  . Location exists: {loc_data['name']}")

        existing_products = {p.name for p in db.query(Product).all()}
        for prod_data in PRODUCTS:
            if prod_data["name"] not in existing_products:
                db.add(Product(**prod_data))
                print(f"  + Product: {prod_data['name']}")
            else:
                print(f"  . Product exists: {prod_data['name']}")

        db.commit()
        print("Seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
