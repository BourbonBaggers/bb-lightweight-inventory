import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Boolean, DateTime, Enum, ForeignKey, Integer, String
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DefaultUnit(str, enum.Enum):
    carton = "carton"
    case = "case"
    unit = "unit"


class Category(str, enum.Enum):
    product = "product"
    product_packaging = "product_packaging"
    other = "other"


class State(str, enum.Enum):
    filled = "filled"
    unfilled = "unfilled"


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    default_unit: Mapped[DefaultUnit] = mapped_column(
        Enum(DefaultUnit, native_enum=False), nullable=False, default=DefaultUnit.unit
    )
    is_inbound: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    counts: Mapped[list["InventoryCount"]] = relationship(back_populates="location")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[Category] = mapped_column(
        Enum(Category, native_enum=False), nullable=False
    )
    has_states: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    cases_per_carton: Mapped[int | None] = mapped_column(Integer, nullable=True)
    units_per_case: Mapped[int | None] = mapped_column(Integer, nullable=True)

    filled_cases_per_carton: Mapped[int | None] = mapped_column(Integer, nullable=True)
    filled_units_per_case: Mapped[int | None] = mapped_column(Integer, nullable=True)
    unfilled_cases_per_carton: Mapped[int | None] = mapped_column(Integer, nullable=True)
    unfilled_units_per_case: Mapped[int | None] = mapped_column(Integer, nullable=True)

    packaging_unit_label: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    counts: Mapped[list["InventoryCount"]] = relationship(back_populates="product")


class InventoryCount(Base):
    __tablename__ = "inventory_counts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), nullable=False)
    state: Mapped[State | None] = mapped_column(
        Enum(State, native_enum=False), nullable=True
    )

    cartons_qty: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    cases_qty: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    units_qty: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    counted_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    is_approximate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    cpc_snapshot: Mapped[int | None] = mapped_column(Integer, nullable=True)
    upc_snapshot: Mapped[int | None] = mapped_column(Integer, nullable=True)

    notes: Mapped[str | None] = mapped_column(String, nullable=True)
    carrier: Mapped[str | None] = mapped_column(String, nullable=True)
    tracking_number: Mapped[str | None] = mapped_column(String, nullable=True)

    product: Mapped["Product"] = relationship(back_populates="counts")
    location: Mapped["Location"] = relationship(back_populates="counts")
