from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class PaymentCreate(BaseModel):
    order_id: int = Field(..., gt=0)
    payment_method: str = Field(default="TEST", min_length=1, max_length=30)


class PaymentResponse(BaseModel):
    id: int
    order_id: int
    user_id: int
    amount: float
    currency: str
    payment_method: str
    transaction_id: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaymentStatusUpdate(BaseModel):
    status: str = Field(
        ...,
        pattern="^(SUCCESS|FAILED|REFUNDED)$",
    )
    transaction_id: Optional[str] = Field(default=None, max_length=200)