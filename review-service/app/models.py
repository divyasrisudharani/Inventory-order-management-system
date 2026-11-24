from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    CheckConstraint,
    UniqueConstraint,
    Index,
)

from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    product_id = Column(Integer, nullable=False, index=True)

    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)

    status = Column(String(20), nullable=False, default="PUBLISHED")
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "rating >= 1 AND rating <= 5",
            name="ck_review_rating",
        ),
        UniqueConstraint(
            "user_id",
            "product_id",
            name="uq_review_user_product",
        ),
        Index("ix_reviews_product_created", "product_id", "created_at"),
    )