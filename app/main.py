from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from app.database import engine, Base
import app.models  # noqa: F401 — registers models with Base before create_all
from app.routes.api import locations as api_locations
from app.routes.api import products as api_products
from app.routes.api import inventory as api_inventory

Base.metadata.create_all(bind=engine)

app = FastAPI(title="BB Inventory")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.include_router(api_locations.router)
app.include_router(api_products.router)
app.include_router(api_inventory.router)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
