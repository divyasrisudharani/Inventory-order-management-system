from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    CheckConstraint,
    Index,
)
from sqlalchemy.orm import relationship

from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, nullable=False, index=True)

    total_amount = Column(Float, nullable=False, default=0.0)

    status = Column(
        String(30),
        nullable=False,
        default="PENDING",
        index=True,
    )

    shipping_address = Column(String(500), nullable=False)

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

    items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint(
            "total_amount >= 0",
            name="ck_order_total_nonnegative",
        ),
        Index("ix_orders_user_created", "user_id", "created_at"),
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)

    order_id = Column(
        Integer,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Product belongs to a separate microservice/database.
    # Therefore, product_id is stored without a local FK.
    product_id = Column(Integer, nullable=False, index=True)

    product_name = Column(String(200), nullable=False)

    quantity = Column(Integer, nullable=False)

    # Store the price at order time so later product price changes
    # do not alter the historical order.
    unit_price = Column(Float, nullable=False)

    subtotal = Column(Float, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    order = relationship(
        "Order",
        back_populates="items",
    )

    __table_args__ = (
        CheckConstraint(
            "quantity > 0",
            name="ck_order_item_quantity_positive",
        ),
        CheckConstraint(
            "unit_price >= 0",
            name="ck_order_item_price_nonnegative",
        ),
        CheckConstraint(
            "subtotal >= 0",
            name="ck_order_item_subtotal_nonnegative",
        ),
    )