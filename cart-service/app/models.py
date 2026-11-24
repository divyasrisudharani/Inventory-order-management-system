from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
    Index,
)

from app.database import Base


# ==========================================
# CART TABLE
# ==========================================

class Cart(Base):
    __tablename__ = "carts"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "product_id",
            name="uq_cart_user_product"
        ),
        CheckConstraint(
            "quantity > 0",
            name="check_cart_quantity_positive"
        ),
        Index("ix_cart_user_id", "user_id"),
    )

    id = Column(Integer, primary_key=True, index=True)

    # User ID comes from the Authentication Service.
    # Product ID comes from the Product Service.
    # These are identifiers from separate services,
    # not database foreign keys.
    user_id = Column(Integer, nullable=False)
    product_id = Column(Integer, nullable=False)

    quantity = Column(Integer, nullable=False, default=1)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )


# ==========================================
# WISHLIST TABLE
# ==========================================

class Wishlist(Base):
    __tablename__ = "wishlists"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "product_id",
            name="uq_wishlist_user_product"
        ),
        Index("ix_wishlist_user_id", "user_id"),
    )

    id = Column(Integer, primary_key=True, index=True)

    # References IDs owned by other microservices.
    # No cross-database foreign keys are used.
    user_id = Column(Integer, nullable=False)
    product_id = Column(Integer, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)