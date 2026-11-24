from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    CheckConstraint,
    Index,
)

from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Inventory(Base):
    __tablename__ = "inventory"

    __table_args__ = (
        CheckConstraint(
            "quantity >= 0",
            name="check_inventory_quantity_nonnegative",
        ),
        CheckConstraint(
            "reserved_quantity >= 0",
            name="check_reserved_quantity_nonnegative",
        ),
        CheckConstraint(
            "reserved_quantity <= quantity",
            name="check_reserved_not_above_quantity",
        ),
        CheckConstraint(
            "low_stock_threshold >= 0",
            name="check_low_stock_threshold_nonnegative",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    product_id = Column(Integer, unique=True, nullable=False, index=True)

    quantity = Column(Integer, nullable=False, default=0)

    reserved_quantity = Column(Integer, nullable=False, default=0)

    low_stock_threshold = Column(Integer, nullable=False, default=10)

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

    @property
    def available_quantity(self):
        return self.quantity - self.reserved_quantity


class StockReservation(Base):
    __tablename__ = "stock_reservations"

    __table_args__ = (
        CheckConstraint(
            "quantity > 0",
            name="check_reservation_quantity_positive",
        ),
        Index("ix_reservation_order_id", "order_id"),
    )

    id = Column(Integer, primary_key=True, index=True)

    product_id = Column(Integer, nullable=False, index=True)

    order_id = Column(String(100), nullable=False)

    quantity = Column(Integer, nullable=False)

    status = Column(
        String(20),
        nullable=False,
        default="RESERVED",
        index=True,
    )

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


class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"

    __table_args__ = (
        CheckConstraint(
            "quantity_change != 0",
            name="check_transaction_quantity_nonzero",
        ),
        Index(
            "ix_inventory_transaction_product_created",
            "product_id",
            "created_at",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    product_id = Column(Integer, nullable=False, index=True)

    quantity_change = Column(Integer, nullable=False)

    transaction_type = Column(String(30), nullable=False)

    reason = Column(String(255), nullable=False)

    responsible_user_id = Column(Integer, nullable=True)

    order_id = Column(String(100), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )