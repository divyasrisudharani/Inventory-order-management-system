import httpx

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ReturnRequest
from app.schemas import (
    ReturnCreate,
    ReturnStatusUpdate,
    RefundStatusUpdate,
    ReturnResponse,
)

router = APIRouter(
    prefix="/returns",
    tags=["Returns and Refunds"],
)

AUTH_SERVICE_URL = "http://127.0.0.1:8001"
ORDER_SERVICE_URL = "http://127.0.0.1:8005"


def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")

    try:
        response = httpx.get(
            f"{AUTH_SERVICE_URL}/auth/me",
            headers={"Authorization": authorization},
            timeout=10.0,
        )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Auth Service unavailable")

    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid access token")

    user = response.json()

    if "id" not in user:
        raise HTTPException(status_code=502, detail="Invalid Auth Service response")

    return {"id": int(user["id"]), "role": user.get("role", "customer")}


def get_order(order_id: int, authorization: str):
    try:
        response = httpx.get(
            f"{ORDER_SERVICE_URL}/orders/{order_id}",
            headers={"Authorization": authorization},
            timeout=10.0,
        )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Order Service unavailable")

    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="Order not found")

    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Could not retrieve order")

    return response.json()


@router.post("/", response_model=ReturnResponse, status_code=201)
def create_return(
    payload: ReturnCreate,
    user: dict = Depends(get_current_user),
    authorization: str = Header(...),
    db: Session = Depends(get_db),
):
    order = get_order(payload.order_id, authorization)

    if int(order.get("user_id", -1)) != user["id"]:
        raise HTTPException(status_code=403, detail="This order does not belong to you")

    if order.get("status") not in {"DELIVERED", "COMPLETED"}:
        raise HTTPException(
            status_code=400,
            detail="Only delivered orders can be returned",
        )

    items = order.get("items", [])
    item = next(
        (
            entry for entry in items
            if int(entry.get("id", -1)) == payload.order_item_id
        ),
        None,
    )

    if item is None:
        raise HTTPException(status_code=404, detail="Order item not found")

    if payload.quantity > int(item.get("quantity", 0)):
        raise HTTPException(
            status_code=400,
            detail="Return quantity exceeds the purchased quantity",
        )

    product_id = int(item["product_id"])
    unit_price = float(item["unit_price"])
    refund_amount = round(unit_price * payload.quantity, 2)

    existing = db.query(ReturnRequest).filter(
        ReturnRequest.order_item_id == payload.order_item_id,
        ReturnRequest.user_id == user["id"],
        ReturnRequest.status.notin_(["REJECTED"]),
    ).all()

    already_requested = sum(record.quantity for record in existing)

    if already_requested + payload.quantity > int(item["quantity"]):
        raise HTTPException(
            status_code=409,
            detail="Requested return quantity exceeds the remaining quantity",
        )

    return_request = ReturnRequest(
        order_id=payload.order_id,
        order_item_id=payload.order_item_id,
        user_id=user["id"],
        product_id=product_id,
        quantity=payload.quantity,
        reason=payload.reason,
        description=payload.description,
        status="REQUESTED",
        refund_amount=refund_amount,
        refund_status="NOT_STARTED",
    )

    db.add(return_request)
    db.commit()
    db.refresh(return_request)

    return return_request


@router.get("/my", response_model=list[ReturnResponse])
def get_my_returns(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(ReturnRequest)
        .filter(ReturnRequest.user_id == user["id"])
        .order_by(ReturnRequest.created_at.desc())
        .all()
    )


@router.get("/{return_id}", response_model=ReturnResponse)
def get_return(
    return_id: int,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = db.query(ReturnRequest).filter(
        ReturnRequest.id == return_id,
        ReturnRequest.user_id == user["id"],
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="Return request not found")

    return record


@router.patch("/{return_id}/status", response_model=ReturnResponse)
def update_return_status(
    return_id: int,
    payload: ReturnStatusUpdate,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user["role"] not in {"administrator", "inventory_manager"}:
        raise HTTPException(status_code=403, detail="Administrator access required")

    record = db.query(ReturnRequest).filter(
        ReturnRequest.id == return_id
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="Return request not found")

    if record.status in {"REJECTED", "COMPLETED"}:
        raise HTTPException(status_code=400, detail="Return request is already closed")

    allowed_transitions = {
        "REQUESTED": {"APPROVED", "REJECTED"},
        "APPROVED": {"RECEIVED"},
        "RECEIVED": {"COMPLETED"},
    }

    if payload.status not in allowed_transitions.get(record.status, set()):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot change status from {record.status} to {payload.status}",
        )

    record.status = payload.status
    db.commit()
    db.refresh(record)

    return record


@router.patch("/{return_id}/refund", response_model=ReturnResponse)
def update_refund_status(
    return_id: int,
    payload: RefundStatusUpdate,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user["role"] != "administrator":
        raise HTTPException(status_code=403, detail="Administrator access required")

    record = db.query(ReturnRequest).filter(
        ReturnRequest.id == return_id
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="Return request not found")

    if record.status != "COMPLETED":
        raise HTTPException(
            status_code=400,
            detail="Return must be completed before refund processing",
        )

    if payload.refund_amount > record.refund_amount:
        raise HTTPException(
            status_code=400,
            detail="Refund amount cannot exceed the eligible refund amount",
        )

    record.refund_status = payload.refund_status
    record.refund_amount = payload.refund_amount

    db.commit()
    db.refresh(record)

    return record