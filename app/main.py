from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import engine, Base
import app.models  # noqa: F401 — registers models with Base before create_all
from app.routes.api import locations as api_locations
from app.routes.api import products as api_products
from app.routes.api import inventory as api_inventory
from app.routes.pages import dashboard as page_dashboard
from app.routes.pages import locations as page_locations
from app.routes.pages import inventory as page_inventory
from app.routes.pages import products as page_products
from app.routes.pages import settings as page_settings
from app.routes.pages import reports as page_reports

Base.metadata.create_all(bind=engine)

def _migrate():
    from sqlalchemy import text
    with engine.connect() as conn:
        conn.execute(text("UPDATE products SET category = 'components' WHERE category = 'product_packaging'"))
        conn.commit()

_migrate()

app = FastAPI(title="BB Inventory")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(api_locations.router)
app.include_router(api_products.router)
app.include_router(api_inventory.router)
app.include_router(page_dashboard.router)
app.include_router(page_locations.router)
app.include_router(page_inventory.router)
app.include_router(page_products.router)
app.include_router(page_settings.router)
app.include_router(page_reports.router)
