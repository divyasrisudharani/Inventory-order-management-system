from decimal import Decimal
from uuid import uuid4
import os
from pathlib import Path
from dotenv import load_dotenv

import httpx
from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Payment
from app.schemas import PaymentCreate, PaymentResponse
ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ROOT_ENV)

PAYMENT_SERVICE_TOKEN = os.getenv("PAYMENT_SERVICE_TOKEN")
router = APIRouter(prefix="/payments", tags=["Payments"])

AUTH_SERVICE_URL = "http://127.0.0.1:8001"
ORDER_SERVICE_URL = "http://127.0.0.1:8005"


def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Bearer token required",
        )

    try:
        response = httpx.get(
            f"{AUTH_SERVICE_URL}/auth/me",
            headers={"Authorization": authorization},
            timeout=10.0,
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Auth Service is unavailable",
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired access token",
        )

    user = response.json()

    if "id" not in user:
        raise HTTPException(
            status_code=502,
            detail="Auth Service response is missing the user ID",
        )

    return {
        "id": int(user["id"]),
        "role": user.get("role", "customer"),
    }


def get_order(order_id: int, authorization: str):
    try:
        response = httpx.get(
            f"{ORDER_SERVICE_URL}/orders/{order_id}",
            headers={"Authorization": authorization},
            timeout=10.0,
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Order Service is unavailable",
        )

    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="Order not found")

    if response.status_code == 401:
        raise HTTPException(
            status_code=401,
            detail="Authentication failed in Order Service",
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail="Could not retrieve order details",
        )

    return response.json()


@router.post(
    "",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_test_payment(
    payload: PaymentCreate,
    user: dict = Depends(get_current_user),
    authorization: str = Header(...),
    db: Session = Depends(get_db),
):
    # Fetch the order through Order Service.
    order = get_order(payload.order_id, authorization)

    if int(order.get("user_id", -1)) != user["id"]:
        raise HTTPException(
            status_code=403,
            detail="You cannot pay for another user's order",
        )

    if order.get("status") in {"CANCELLED", "DELIVERED"}:
        raise HTTPException(
            status_code=400,
            detail="This order cannot be paid for",
        )

    try:
        amount = Decimal(str(order["total_amount"]))
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Order contains an invalid total amount",
        )

    if not amount.is_finite() or amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Order amount must be greater than zero",
        )

    existing = (
        db.query(Payment)
        .filter(
            Payment.order_id == payload.order_id,
            Payment.user_id == user["id"],
            Payment.status == "SUCCESS",
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="This order already has a successful payment",
        )

    payment = Payment(
        order_id=payload.order_id,
        user_id=user["id"],
        amount=float(amount),
        currency="INR",
        payment_method=payload.payment_method,
        transaction_id=f"TEST-{uuid4().hex}",
        status="SUCCESS",
    )

   
    db.add(payment)

    try:
        db.commit()
        db.refresh(payment)

    except Exception:
        db.rollback()
        raise HTTPException(
        status_code=500,
        detail="Could not save payment",
        )

# Notify Order Service after successful payment
    try:
        response = httpx.post(
        f"{ORDER_SERVICE_URL}/orders/{payment.order_id}/confirm-payment",
        headers={
            "X-Service-Token": PAYMENT_SERVICE_TOKEN
        },
        timeout=10.0,
        )

        if response.status_code != 200:
           raise HTTPException(
            status_code=502,
            detail="Payment succeeded, but order confirmation failed. Retry confirmation.",
        )

    except httpx.RequestError:
        raise HTTPException(
        status_code=503,
        detail="Payment succeeded, but Order Service is unavailable. Retry confirmation.",
        )

    return payment



@router.get("", response_model=list[PaymentResponse])
def get_my_payments(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Payment)
        .filter(Payment.user_id == user["id"])
        .order_by(Payment.created_at.desc())
        .all()
    )


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: int,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    payment = (
        db.query(Payment)
        .filter(
            Payment.id == payment_id,
            Payment.user_id == user["id"],
        )
        .first()
    )

    if not payment:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    return payment