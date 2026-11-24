from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ==========================================
# CART SCHEMAS
# ==========================================

class CartCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(default=1, gt=0)


class CartUpdate(BaseModel):
    quantity: int = Field(gt=0)


class CartResponse(BaseModel):
    id: int
    user_id: int
    product_id: int
    quantity: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# WISHLIST SCHEMAS
# ==========================================

class WishlistCreate(BaseModel):
    product_id: int = Field(gt=0)


class WishlistResponse(BaseModel):
    id: int
    user_id: int
    product_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# CART SUMMARY SCHEMA
# ==========================================

class CartItemSummary(BaseModel):
    product_id: int
    product_name: str
    price: float
    quantity: int
    subtotal: float


class CartSummary(BaseModel):
    items: list[CartItemSummary]
    total_items: int
    total_amount: float