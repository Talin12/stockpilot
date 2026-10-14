from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

StockStatus = Literal["IN_STOCK", "LOW_STOCK", "OUT_OF_STOCK"]
MovementType = Literal["RECEIVED", "SHIPPED", "ADJUSTED"]


class ProductBase(BaseModel):
    sku: str = Field(min_length=2, max_length=40, pattern=r"^[A-Za-z0-9][A-Za-z0-9\-_.]*$")
    name: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1, max_length=80)
    description: str = Field(default="", max_length=2000)
    reorder_level: int = Field(default=10, ge=0, le=1_000_000)
    unit_price: float = Field(default=0, ge=0, le=10_000_000)
    supplier: str = Field(default="", max_length=120)
    location: str = Field(default="", max_length=80)


class ProductCreate(ProductBase):
    # Opening balance; recorded as the first RECEIVED movement in the ledger.
    quantity: int = Field(default=0, ge=0, le=1_000_000)


class ProductUpdate(BaseModel):
    """Partial update. Quantity is deliberately absent: stock only changes via movements."""

    sku: str | None = Field(
        default=None, min_length=2, max_length=40, pattern=r"^[A-Za-z0-9][A-Za-z0-9\-_.]*$"
    )
    name: str | None = Field(default=None, min_length=1, max_length=200)
    category: str | None = Field(default=None, min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=2000)
    reorder_level: int | None = Field(default=None, ge=0, le=1_000_000)
    unit_price: float | None = Field(default=None, ge=0, le=10_000_000)
    supplier: str | None = Field(default=None, max_length=120)
    location: str | None = Field(default=None, max_length=80)


class ProductOut(ProductBase):
    id: int
    quantity: int
    stock_status: StockStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MovementCreate(BaseModel):
    movement_type: MovementType
    quantity: int = Field(
        description="Units moved. RECEIVED/SHIPPED must be positive; ADJUSTED is a signed correction."
    )
    note: str = Field(default="", max_length=255)

    @model_validator(mode="after")
    def check_quantity(self) -> "MovementCreate":
        if self.quantity == 0:
            raise ValueError("quantity must not be zero")
        if self.movement_type != "ADJUSTED" and self.quantity < 0:
            raise ValueError(f"{self.movement_type} quantity must be positive")
        if abs(self.quantity) > 1_000_000:
            raise ValueError("quantity is too large")
        return self


class MovementOut(BaseModel):
    id: int
    product_id: int
    product_sku: str
    product_name: str
    movement_type: MovementType
    quantity_change: int
    balance_after: int
    note: str
    created_at: datetime


class CategorySummary(BaseModel):
    category: str
    products: int
    units: int
    value: float


class StatsOut(BaseModel):
    total_products: int
    total_units: int
    inventory_value: float
    low_stock: int
    out_of_stock: int
    categories: list[CategorySummary]


class InfoOut(BaseModel):
    service: str
    version: str
    environment: str
    git_sha: str
