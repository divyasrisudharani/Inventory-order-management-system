from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    CheckConstraint,
    Index,
)

from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)

    amount = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False, default="INR")

    payment_method = Column(String(30), nullable=False, default="TEST")
    transaction_id = Column(String(200), nullable=True, unique=True)

    status = Column(
        String(30),
        nullable=False,
        default="PENDING",
        index=True,
    )

    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_payment_amount_positive"),
        Index("ix_payments_user_order", "user_id", "order_id"),
    )