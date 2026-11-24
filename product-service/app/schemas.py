from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
)


class ProductCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)

    description: str = Field(min_length=5)

    category: str = Field(min_length=2, max_length=100)

    brand: str = Field(min_length=2, max_length=100)

    price: float = Field(gt=0, allow_inf_nan=False)

    image_url: HttpUrl | None = None

    rating: float = Field(default=0.0, ge=0, le=5)


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)

    description: str | None = Field(default=None, min_length=5)

    category: str | None = Field(default=None, min_length=2, max_length=100)

    brand: str | None = Field(default=None, min_length=2, max_length=100)

    price: float | None = Field(default=None, gt=0, allow_inf_nan=False)

    image_url: HttpUrl | None = None

    rating: float | None = Field(default=None, ge=0, le=5)


class ProductResponse(BaseModel):
    id: int
    name: str
    description: str
    category: str
    brand: str
    price: float
    image_url: str | None
    rating: float
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)