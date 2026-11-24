from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
)

from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(150), nullable=False, index=True)

    description = Column(Text, nullable=False)

    category = Column(String(100), nullable=False, index=True)

    brand = Column(String(100), nullable=False)

    price = Column(Float, nullable=False)

    image_url = Column(String(500), nullable=True)

    rating = Column(Float, nullable=False, default=0.0)

    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )