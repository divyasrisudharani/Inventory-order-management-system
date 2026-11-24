from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


# --------------------------------------------------
# ORDER ITEM RESPONSE
# --------------------------------------------------

class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: int
    unit_price: float
    subtotal: float

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------
# ORDER CREATION REQUEST
# --------------------------------------------------

class OrderCreate(BaseModel):
    shipping_address: str = Field(
        ...,
        min_length=5,
        max_length=500,
    )


# --------------------------------------------------
# ORDER STATUS UPDATE
# --------------------------------------------------

class OrderStatusUpdate(BaseModel):
    status: str = Field(
        ...,
        pattern="^(CONFIRMED|SHIPPED|DELIVERED|CANCELLED)$",
    )


# --------------------------------------------------
# ORDER RESPONSE
# --------------------------------------------------

class OrderResponse(BaseModel):
    id: int
    user_id: int
    total_amount: float
    status: str
    shipping_address: str
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse]

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------
# ORDER LIST RESPONSE
# --------------------------------------------------

class OrderListResponse(BaseModel):
    orders: List[OrderResponse]
    total_orders: int


# --------------------------------------------------
# OPTIONAL ERROR RESPONSE
# --------------------------------------------------

class OrderMessageResponse(BaseModel):
    message: str
    order_id: Optional[int] = None