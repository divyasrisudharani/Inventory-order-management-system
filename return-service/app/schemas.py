from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class ReturnCreate(BaseModel):
    order_id: int = Field(..., gt=0)
    order_item_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)
    reason: str = Field(..., min_length=3, max_length=250)
    description: str | None = Field(default=None, max_length=2000)


class ReturnStatusUpdate(BaseModel):
    status: str = Field(
        ...,
        pattern="^(APPROVED|REJECTED|RECEIVED|COMPLETED)$",
    )


class RefundStatusUpdate(BaseModel):
    refund_status: str = Field(
        ...,
        pattern="^(PENDING|PROCESSING|COMPLETED|FAILED)$",
    )
    refund_amount: float = Field(..., ge=0)


class ReturnResponse(BaseModel):
    id: int
    order_id: int
    order_item_id: int
    user_id: int
    product_id: int
    quantity: int
    reason: str
    description: str | None
    status: str
    refund_amount: float
    refund_status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)