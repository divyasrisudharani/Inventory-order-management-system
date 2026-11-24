from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Coupon
from app.schemas import (
    CouponCreate,
    CouponApply,
    CouponResponse,
    CouponCalculationResponse,
)

router = APIRouter(prefix="/coupons", tags=["Coupons"])


@router.post("/", response_model=CouponResponse, status_code=201)
def create_coupon(
    payload: CouponCreate,
    db: Session = Depends(get_db),
):
    code = payload.code.strip().upper()

    if not code:
        raise HTTPException(status_code=400, detail="Coupon code is required")

    existing = db.query(Coupon).filter(Coupon.code == code).first()

    if existing:
        raise HTTPException(status_code=409, detail="Coupon code already exists")

    if payload.discount_type == "PERCENTAGE" and payload.discount_value > 100:
        raise HTTPException(
            status_code=400,
            detail="Percentage discount cannot exceed 100",
        )

    if (
        payload.discount_type == "FIXED"
        and payload.maximum_discount is not None
    ):
        raise HTTPException(
            status_code=400,
            detail="maximum_discount is only applicable to percentage coupons",
        )

    coupon = Coupon(
        code=code,
        description=payload.description,
        discount_type=payload.discount_type,
        discount_value=payload.discount_value,
        minimum_order_amount=payload.minimum_order_amount,
        maximum_discount=payload.maximum_discount,
        usage_limit=payload.usage_limit,
        expires_at=payload.expires_at,
    )

    db.add(coupon)
    db.commit()
    db.refresh(coupon)

    return coupon


@router.get("/", response_model=list[CouponResponse])
def list_coupons(db: Session = Depends(get_db)):
    return db.query(Coupon).order_by(Coupon.id.desc()).all()


@router.post("/calculate", response_model=CouponCalculationResponse)
def calculate_discount(
    payload: CouponApply,
    db: Session = Depends(get_db),
):
    code = payload.code.strip().upper()

    coupon = db.query(Coupon).filter(Coupon.code == code).first()

    if not coupon or not coupon.is_active:
        raise HTTPException(status_code=404, detail="Invalid or inactive coupon")

    now = datetime.now(timezone.utc)

    if coupon.expires_at is not None:
        expiry = coupon.expires_at

        # SQLite may return a naive datetime even when timezone=True.
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)

        if expiry <= now:
            raise HTTPException(status_code=400, detail="Coupon has expired")

    if coupon.usage_limit is not None and coupon.times_used >= coupon.usage_limit:
        raise HTTPException(status_code=400, detail="Coupon usage limit reached")

    if payload.order_amount < coupon.minimum_order_amount:
        raise HTTPException(
            status_code=400,
            detail=f"Minimum order amount is {coupon.minimum_order_amount}",
        )

    if coupon.discount_type == "PERCENTAGE":
        discount = payload.order_amount * coupon.discount_value / 100

        if coupon.maximum_discount is not None:
            discount = min(discount, coupon.maximum_discount)
    else:
        discount = coupon.discount_value

    discount = round(min(discount, payload.order_amount), 2)
    final_amount = round(payload.order_amount - discount, 2)

    # Calculation only: do not increment times_used here.
    # Count usage only when a valid order actually completes checkout.
    return CouponCalculationResponse(
        code=coupon.code,
        order_amount=payload.order_amount,
        discount_amount=discount,
        final_amount=final_amount,
        message="Coupon calculated successfully",
    )


@router.patch("/{coupon_id}/deactivate")
def deactivate_coupon(
    coupon_id: int,
    db: Session = Depends(get_db),
):
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()

    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")

    coupon.is_active = False
    db.commit()

    return {"message": "Coupon deactivated successfully"}