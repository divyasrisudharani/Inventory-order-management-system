from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    CheckConstraint,
    Index,
)

from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Coupon(Base):
    __tablename__ = "coupons"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(250), nullable=True)

    discount_type = Column(String(20), nullable=False)
    discount_value = Column(Float, nullable=False)

    minimum_order_amount = Column(Float, nullable=False, default=0.0)
    maximum_discount = Column(Float, nullable=True)

    usage_limit = Column(Integer, nullable=True)
    times_used = Column(Integer, nullable=False, default=0)

    is_active = Column(Boolean, nullable=False, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "discount_type IN ('PERCENTAGE', 'FIXED')",
            name="ck_coupon_discount_type",
        ),
        CheckConstraint(
            "discount_value > 0",
            name="ck_coupon_discount_value_positive",
        ),
        CheckConstraint(
            "minimum_order_amount >= 0",
            name="ck_coupon_min_order_nonnegative",
        ),
        CheckConstraint(
            "times_used >= 0",
            name="ck_coupon_times_used_nonnegative",
        ),
        Index("ix_coupon_active_expiry", "is_active", "expires_at"),
    )