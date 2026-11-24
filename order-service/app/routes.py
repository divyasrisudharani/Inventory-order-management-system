from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
import httpx
import asyncio
import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import Request
from app.rabbitmq_publisher import publish_order_created

logger = logging.getLogger(__name__)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    status,
)

bearer_scheme = HTTPBearer()
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Order, OrderItem
from app.schemas import (
    OrderCreate,
    OrderResponse,
    OrderListResponse,
)
ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ROOT_ENV)

PAYMENT_SERVICE_TOKEN = os.getenv("PAYMENT_SERVICE_TOKEN")
ORDER_SERVICE_TOKEN = os.getenv("ORDER_SERVICE_TOKEN")
router = APIRouter(prefix="/orders", tags=["Orders"])


# --------------------------------------------------
# MICROSERVICE URLS
# --------------------------------------------------

AUTH_SERVICE_URL = "http://127.0.0.1:8001"
PRODUCT_SERVICE_URL = "http://127.0.0.1:8002"
CART_SERVICE_URL = "http://127.0.0.1:8003"
INVENTORY_SERVICE_URL = "http://127.0.0.1:8004"


# --------------------------------------------------
# HTTP HELPERS
# --------------------------------------------------

def service_get(url: str, token: str):
    try:
        response = httpx.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0,
        )
        return response

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="A dependent service timed out",
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="A dependent service is unavailable",
        )


def service_post(url: str, token: str, payload: dict):
    try:
        response = httpx.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0,
        )
        return response

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="A dependent service timed out",
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="A dependent service is unavailable",
        )


# --------------------------------------------------
# AUTHENTICATION
# --------------------------------------------------

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    token = credentials.credentials

    response = service_get(
        f"{AUTH_SERVICE_URL}/auth/me",
        token,
    )

    if response.status_code >= 400:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired access token",
        )

    user = response.json()
    user["token"] = token

    return user


# --------------------------------------------------
# CREATE ORDER
# --------------------------------------------------

@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_order(
    data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["id"]
    token = current_user["token"]

    # 1. Retrieve the authenticated user's cart.
    cart_response = service_get(
        f"{CART_SERVICE_URL}/cart",
        token,
    )

    if cart_response.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail="Could not retrieve your cart",
        )

    cart_data = cart_response.json()
    cart_items = cart_data.get("items", [])

    if not cart_items:
        raise HTTPException(
            status_code=400,
            detail="Your cart is empty",
        )

    # 2. Validate each product and calculate prices server-side.
    validated_items = []
    total_amount = Decimal("0.00")

    for cart_item in cart_items:
        product_id = int(cart_item["product_id"])
        quantity = int(cart_item["quantity"])

        if quantity <= 0:
            raise HTTPException(
                status_code=400,
                detail="Cart contains an invalid quantity",
            )

        product_response = service_get(
            f"{PRODUCT_SERVICE_URL}/products/{product_id}",
            token,
        )

        if product_response.status_code == 404:
            raise HTTPException(
                status_code=400,
                detail=f"Product {product_id} no longer exists",
            )

        if product_response.status_code >= 400:
            raise HTTPException(
                status_code=502,
                detail=f"Could not verify product {product_id}",
            )

        product = product_response.json()

        if product.get("is_active") is False:
            raise HTTPException(
                status_code=400,
                detail=f"Product {product_id} is unavailable",
            )

        unit_price = Decimal(str(product["price"])).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        subtotal = (unit_price * quantity).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        total_amount += subtotal

        validated_items.append({
            "product_id": product_id,
            "product_name": product["name"],
            "quantity": quantity,
            "unit_price": unit_price,
            "subtotal": subtotal,
        })

    # 3. Create the pending order in the local database.
    order = Order(
        user_id=user_id,
        total_amount=float(total_amount),
        status="PENDING",
        shipping_address=data.shipping_address.strip(),
    )

    for item in validated_items:
        order.items.append(
            OrderItem(
                product_id=item["product_id"],
                product_name=item["product_name"],
                quantity=item["quantity"],
                unit_price=float(item["unit_price"]),
                subtotal=float(item["subtotal"]),
            )
        )

    db.add(order)

    try:
        db.commit()
        db.refresh(order)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not create the order",
        )

    # 4. Reserve stock for every order item.
    #
    # IMPORTANT:
    # The exact inventory API payload must match your inventory
    # service. This assumes POST /inventory/reserve accepts:
    # product_id, order_id, quantity.
    reserved_items = []

    try:
        for item in validated_items:
            response = service_post(
                f"{INVENTORY_SERVICE_URL}/inventory/reservations",
                token,
                {
                    "product_id": item["product_id"],
                    "order_id": str(order.id),
                    "quantity": item["quantity"],
                },
            )

            if response.status_code >= 400:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        f"Could not reserve stock for product "
                        f"{item['product_id']}. The order will be cancelled."
                    ),
                )

            reserved_items.append(item)

    except Exception:
        # Release any stock already reserved for this order.
        # This assumes POST /inventory/release accepts product_id
        # and order_id. Adjust it to match the real inventory API.
        for item in reserved_items:
            try:
                httpx.post(
                    f"{INVENTORY_SERVICE_URL}/inventory/release",
                    json={
                        "product_id": item["product_id"],
                        "order_id": str(order.id),
                    },
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10.0,
                )
            except httpx.RequestError:
                pass

        order.status = "CANCELLED"
        db.commit()

        raise HTTPException(
            status_code=409,
            detail=(
                f"Order {order.id} was cancelled because stock "
                "could not be reserved. Verify inventory before retrying."
            ),
        )
    try:
        asyncio.run(
             publish_order_created({
                   "event": "order_created",
                    "user_id": order.user_id,
                    "order_id": order.id,
                    "total_amount": order.total_amount,
                  })
        )
    except Exception:
                logger.exception(
                  "Order was created, but RabbitMQ publishing failed."
                )
    return order


# --------------------------------------------------
# GET CURRENT USER'S ORDERS
# --------------------------------------------------

# GET CURRENT USER'S ORDERS
@router.get("", response_model=OrderListResponse)
def get_my_orders(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    query = db.query(Order)

    # Administrator can view all customers' orders
    if current_user.get("role") != "administrator":
        query = query.filter(
            Order.user_id == current_user["id"]
        )

    orders = (
        query
        .order_by(Order.created_at.desc())
        .all()
    )

    return {
        "orders": orders,
        "total_orders": len(orders),
    }


# --------------------------------------------------
# GET ONE ORDER
# --------------------------------------------------

@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    query = db.query(Order).filter(Order.id == order_id)

    if current_user.get("role") != "administrator":
        query = query.filter(
            Order.user_id == current_user["id"]
        )

    order = query.first()

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    return order


# --------------------------------------------------
# CONFIRM SUCCESSFUL PAYMENT
# --------------------------------------------------

@router.post("/{order_id}/confirm-payment")
def confirm_payment(
    order_id: int,
    x_service_token: str = Header(...),
    db: Session = Depends(get_db),
):
    expected_token = PAYMENT_SERVICE_TOKEN

    if not expected_token or x_service_token != expected_token:
        raise HTTPException(
            status_code=403,
            detail="Invalid payment service credentials",
        )

    order = (
        db.query(Order)
        .filter(Order.id == order_id)
        .first()
    )

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    if order.status == "CONFIRMED":
        return {
            "message": "Order already confirmed",
            "order_id": order.id,
            "status": order.status,
        }

    if order.status != "PENDING":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot confirm order with status {order.status}",
        )

    order.status = "CONFIRMED"
    db.commit()
    db.refresh(order)

    return {
        "message": "Payment confirmed and order updated",
        "order_id": order.id,
        "status": order.status,
    }


# --------------------------------------------------
# CANCEL ORDER
# --------------------------------------------------

@router.post("/{order_id}/cancel")
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    order = (
        db.query(Order)
        .filter(
            Order.id == order_id,
            Order.user_id == current_user["id"],
        )
        .first()
    )

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    if order.status != "PENDING":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel order with status {order.status}",
        )

    try:
        response = httpx.post(
            f"{INVENTORY_SERVICE_URL}/inventory/orders/{order_id}/release",
            headers={
                "X-Service-Token": ORDER_SERVICE_TOKEN
            },
            timeout=10.0,
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail="Could not release inventory reservations",
            )

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Inventory Service is unavailable",
        )

    order.status = "CANCELLED"
    db.commit()

    return {
        "message": "Order cancelled and inventory released",
        "order_id": order.id,
        "status": order.status,
    }