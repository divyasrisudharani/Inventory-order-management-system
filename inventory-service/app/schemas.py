from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class InventoryCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(ge=0)
    low_stock_threshold: int = Field(default=10, ge=0)


class StockAdjustment(BaseModel):
    quantity_change: int = Field(
        description="Positive to add stock; negative to deduct stock",
        ne=0,
    )
    reason: str = Field(min_length=3, max_length=255)
    transaction_type: Literal[
        "STOCK_IN",
        "STOCK_OUT",
        "ADJUSTMENT",
    ] = "ADJUSTMENT"


class InventoryResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    reserved_quantity: int
    available_quantity: int
    low_stock_threshold: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StockReservationCreate(BaseModel):
    product_id: int = Field(gt=0)
    order_id: str = Field(min_length=1, max_length=100)
    quantity: int = Field(gt=0)


class StockReservationResponse(BaseModel):
    id: int
    product_id: int
    order_id: str
    quantity: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InventoryTransactionResponse(BaseModel):
    id: int
    product_id: int
    quantity_change: int
    transaction_type: str
    reason: str
    responsible_user_id: int | None
    order_id: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)