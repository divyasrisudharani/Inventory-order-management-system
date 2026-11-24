import httpx
import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import Header
from fastapi import Body
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from app.database import get_db
from app.models import Inventory, StockReservation, InventoryTransaction
from app.schemas import (
    InventoryCreate,
    InventoryResponse,
    StockAdjustment,
    StockReservationCreate,
    StockReservationResponse,
    InventoryTransactionResponse,
)
ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ROOT_ENV)

ORDER_SERVICE_TOKEN = os.getenv("ORDER_SERVICE_TOKEN")

router = APIRouter(
    prefix="/inventory",
    tags=["Inventory Management"]
)


# --------------------------------------------------
# PRODUCT SERVICE CONNECTION
# --------------------------------------------------

PRODUCT_SERVICE_URL = "http://127.0.0.1:8002"


def verify_product(product_id: int):
    """
    Verify that the product exists in Product Service.
    Product Service must be running on port 8002.
    """

    try:
        response = httpx.get(
            f"{PRODUCT_SERVICE_URL}/products/{product_id}",
            timeout=5.0
        )

        if response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product ID {product_id} does not exist."
            )

        response.raise_for_status()
        return response.json()

    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Product Service is unavailable."
        )

    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to verify the product with Product Service."
        ) from exc


# --------------------------------------------------
# 1. CREATE INVENTORY
# POST /inventory
# --------------------------------------------------

@router.post(
    "",
    response_model=InventoryResponse,
    status_code=status.HTTP_201_CREATED
)
def create_inventory(
    inventory_data: InventoryCreate,
    db: Session = Depends(get_db)
):
    # Verify the product before creating inventory.
    verify_product(inventory_data.product_id)

    existing_inventory = (
        db.query(Inventory)
        .filter(
            Inventory.product_id == inventory_data.product_id
        )
        .first()
    )

    if existing_inventory:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Inventory already exists for this product."
        )

    inventory = Inventory(
        product_id=inventory_data.product_id,
        quantity=inventory_data.quantity,
        reserved_quantity=0,
        low_stock_threshold=inventory_data.low_stock_threshold
    )

    db.add(inventory)

    # Record initial stock when quantity is greater than zero.
    if inventory_data.quantity > 0:
        transaction = InventoryTransaction(
            product_id=inventory_data.product_id,
            quantity_change=inventory_data.quantity,
            transaction_type="STOCK_IN",
            reason="Initial inventory creation"
        )
        db.add(transaction)

    try:
        db.commit()
        db.refresh(inventory)

    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Inventory already exists or violates a database constraint."
        ) from exc

    return inventory


# --------------------------------------------------
# 2. GET ALL INVENTORY
# GET /inventory
# --------------------------------------------------

@router.get("", response_model=list[InventoryResponse])
def get_all_inventory(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    return (
        db.query(Inventory)
        .order_by(Inventory.id)
        .offset(skip)
        .limit(limit)
        .all()
    )


# --------------------------------------------------
# 3. GET INVENTORY BY PRODUCT ID
# GET /inventory/{product_id}
# --------------------------------------------------

@router.get("/{product_id}", response_model=InventoryResponse)
def get_inventory(
    product_id: int,
    db: Session = Depends(get_db)
):
    inventory = (
        db.query(Inventory)
        .filter(Inventory.product_id == product_id)
        .first()
    )

    if not inventory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory record not found."
        )

    return inventory


# --------------------------------------------------
# 4. ADJUST STOCK
# PATCH /inventory/{product_id}/stock
# --------------------------------------------------

@router.patch("/{product_id}/stock", response_model=InventoryResponse)
def adjust_stock(
    product_id: int,
    adjustment: StockAdjustment,
    db: Session = Depends(get_db)
):
    inventory = (
        db.query(Inventory)
        .filter(Inventory.product_id == product_id)
        .with_for_update()
        .first()
    )

    if not inventory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory record not found."
        )

    new_quantity = inventory.quantity + adjustment.quantity_change

    # Do not remove stock that is already reserved.
    if new_quantity < inventory.reserved_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Insufficient unreserved stock. "
                "The adjustment would reduce stock below reserved quantity."
            )
        )

    inventory.quantity = new_quantity

    transaction = InventoryTransaction(
        product_id=product_id,
        quantity_change=adjustment.quantity_change,
        transaction_type=adjustment.transaction_type,
        reason=adjustment.reason
    )

    db.add(transaction)

    try:
        db.commit()
        db.refresh(inventory)

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update stock."
        ) from exc

    return inventory


# --------------------------------------------------
# 5. RESERVE STOCK FOR AN ORDER
# POST /inventory/reservations
# --------------------------------------------------

@router.post(
    "/reservations",
    response_model=StockReservationResponse,
    status_code=status.HTTP_201_CREATED
)
def reserve_stock(
    reservation_data: StockReservationCreate,
    db: Session = Depends(get_db)
):
    # Verify that the product exists in Product Service.
    verify_product(reservation_data.product_id)

    inventory = (
        db.query(Inventory)
        .filter(
            Inventory.product_id == reservation_data.product_id
        )
        .with_for_update()
        .first()
    )

    if not inventory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory record not found for this product."
        )

    available_quantity = (
        inventory.quantity - inventory.reserved_quantity
    )

    if available_quantity < reservation_data.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Insufficient stock. Available quantity: "
                f"{available_quantity}"
            )
        )

    reservation = StockReservation(
        product_id=reservation_data.product_id,
        order_id=reservation_data.order_id,
        quantity=reservation_data.quantity,
        status="RESERVED"
    )

    inventory.reserved_quantity += reservation_data.quantity

    db.add(reservation)

    try:
        db.commit()
        db.refresh(reservation)

    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Unable to create reservation because of a database constraint."
        ) from exc

    return reservation


# --------------------------------------------------
# 6. RELEASE A STOCK RESERVATION
# POST /inventory/reservations/{reservation_id}/release
# --------------------------------------------------

@router.post(
    "/reservations/{reservation_id}/release",
    response_model=StockReservationResponse
)
def release_reservation(
    reservation_id: int,
    db: Session = Depends(get_db)
):
    reservation = (
        db.query(StockReservation)
        .filter(StockReservation.id == reservation_id)
        .first()
    )

    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock reservation not found."
        )

    if reservation.status != "RESERVED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Cannot release reservation with status "
                f"{reservation.status}."
            )
        )

    inventory = (
        db.query(Inventory)
        .filter(
            Inventory.product_id == reservation.product_id
        )
        .first()
    )

    if not inventory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory record not found."
        )

    inventory.reserved_quantity -= reservation.quantity
    reservation.status = "RELEASED"

    try:
        db.commit()
        db.refresh(reservation)

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to release stock reservation."
        ) from exc

    return reservation


# --------------------------------------------------
# 7. GET INVENTORY TRANSACTION HISTORY
# GET /inventory/{product_id}/transactions
# --------------------------------------------------

@router.get(
    "/{product_id}/transactions",
    response_model=list[InventoryTransactionResponse]
)
def get_inventory_transactions(
    product_id: int,
    db: Session = Depends(get_db)
):
    inventory = (
        db.query(Inventory)
        .filter(Inventory.product_id == product_id)
        .first()
    )

    if not inventory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory record not found."
        )

    return (
        db.query(InventoryTransaction)
        .filter(InventoryTransaction.product_id == product_id)
        .order_by(InventoryTransaction.created_at.desc())
        .all()
    )
# --------------------------------------------------
# RELEASE ALL RESERVATIONS FOR AN ORDER
# POST /inventory/orders/{order_id}/release
# --------------------------------------------------

@router.post("/orders/{order_id}/release")
def release_order_reservations(
    order_id: int,
    x_service_token: str =Header(...),
    db: Session = Depends(get_db)
):
    if not ORDER_SERVICE_TOKEN or x_service_token != ORDER_SERVICE_TOKEN:
       raise HTTPException(status_code=403,detail="Invalid Order Service credentials")
    reservations = (
        db.query(StockReservation)
        .filter(
            StockReservation.order_id == order_id,
            StockReservation.status == "RESERVED"
        )
        .with_for_update()
        .all()
    )

    if not reservations:
        return {
            "message": "No active reservations found",
            "order_id": order_id,
            "released_count": 0
        }

    try:
        released_count = 0

        for reservation in reservations:
            inventory = (
                db.query(Inventory)
                .filter(
                    Inventory.product_id == reservation.product_id
                )
                .with_for_update()
                .first()
            )

            if not inventory:
                raise HTTPException(
                    status_code=404,
                    detail=f"Inventory not found for product {reservation.product_id}"
                )

            inventory.reserved_quantity -= reservation.quantity

            if inventory.reserved_quantity < 0:
                raise HTTPException(
                    status_code=409,
                    detail="Invalid reserved inventory quantity"
                )

            reservation.status = "RELEASED"
            released_count += 1

        db.commit()

        return {
            "message": "Order reservations released successfully",
            "order_id": order_id,
            "released_count": released_count
        }

    except Exception:
        db.rollback()
        raise