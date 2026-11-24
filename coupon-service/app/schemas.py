from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class CouponCreate(BaseModel):
    code: str = Field(..., min_length=3, max_length=50)
    description: str | None = Field(default=None, max_length=250)

    discount_type: str = Field(
        ...,
        pattern="^(PERCENTAGE|FIXED)$",
    )
    discount_value: float = Field(..., gt=0)

    minimum_order_amount: float = Field(default=0, ge=0)
    maximum_discount: float | None = Field(default=None, gt=0)

    usage_limit: int | None = Field(default=None, gt=0)
    expires_at: datetime | None = None


class CouponApply(BaseModel):
    code: str = Field(..., min_length=3, max_length=50)
    order_amount: float = Field(..., gt=0)


class CouponResponse(BaseModel):
    id: int
    code: str
    description: str | None
    discount_type: str
    discount_value: float
    minimum_order_amount: float
    maximum_discount: float | None
    usage_limit: int | None
    times_used: int
    is_active: bool
    expires_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CouponCalculationResponse(BaseModel):
    code: str
    order_amount: float
    discount_amount: float
    final_amount: float
    message: str