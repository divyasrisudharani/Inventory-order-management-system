from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    DateTime,
    CheckConstraint,
    Index,
)

from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class ReturnRequest(Base):
    __tablename__ = "return_requests"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, nullable=False, index=True)
    order_item_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    product_id = Column(Integer, nullable=False, index=True)

    quantity = Column(Integer, nullable=False)
    reason = Column(String(250), nullable=False)
    description = Column(Text, nullable=True)

    status = Column(
        String(30),
        nullable=False,
        default="REQUESTED",
        index=True,
    )

    refund_amount = Column(Float, nullable=False, default=0.0)
    refund_status = Column(
        String(30),
        nullable=False,
        default="NOT_STARTED",
    )

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_return_quantity_positive"),
        CheckConstraint("refund_amount >= 0", name="ck_refund_amount_nonnegative"),
        Index("ix_returns_user_created", "user_id", "created_at"),
    )