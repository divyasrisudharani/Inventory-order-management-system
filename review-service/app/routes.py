import httpx

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Review
from app.schemas import ReviewCreate, ReviewUpdate, ReviewResponse

router = APIRouter(prefix="/reviews", tags=["Reviews"])

AUTH_SERVICE_URL = "http://127.0.0.1:8001"
PRODUCT_SERVICE_URL = "http://127.0.0.1:8002"


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


def verify_product(product_id: int):
    try:
        response = httpx.get(
            f"{PRODUCT_SERVICE_URL}/products/{product_id}",
            timeout=10.0,
        )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Product Service unavailable")

    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="Product not found")

    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Could not verify product")

    product = response.json()

    if product.get("is_active") is False:
        raise HTTPException(status_code=400, detail="Product is inactive")

    return product


@router.post("/", response_model=ReviewResponse, status_code=201)
def create_review(
    payload: ReviewCreate,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    verify_product(payload.product_id)

    existing = db.query(Review).filter(
        Review.user_id == user["id"],
        Review.product_id == payload.product_id,
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="You have already reviewed this product",
        )

    review = Review(
        user_id=user["id"],
        product_id=payload.product_id,
        rating=payload.rating,
        comment=payload.comment,
    )

    db.add(review)

    try:
        db.commit()
        db.refresh(review)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=409, detail="Could not create review")

    return review


@router.get("/product/{product_id}", response_model=list[ReviewResponse])
def get_product_reviews(
    product_id: int,
    db: Session = Depends(get_db),
):
    verify_product(product_id)

    return (
        db.query(Review)
        .filter(Review.product_id == product_id, Review.status == "PUBLISHED")
        .order_by(Review.created_at.desc())
        .all()
    )


@router.get("/my", response_model=list[ReviewResponse])
def get_my_reviews(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Review)
        .filter(Review.user_id == user["id"])
        .order_by(Review.created_at.desc())
        .all()
    )


@router.put("/{review_id}", response_model=ReviewResponse)
def update_review(
    review_id: int,
    payload: ReviewUpdate,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    review = db.query(Review).filter(
        Review.id == review_id,
        Review.user_id == user["id"],
    ).first()

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    changes = payload.model_dump(exclude_unset=True)

    if not changes:
        raise HTTPException(status_code=400, detail="No update fields provided")

    for field, value in changes.items():
        setattr(review, field, value)

    db.commit()
    db.refresh(review)

    return review


@router.delete("/{review_id}")
def delete_review(
    review_id: int,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    review = db.query(Review).filter(
        Review.id == review_id,
        Review.user_id == user["id"],
    ).first()

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    db.delete(review)
    db.commit()

    return {"message": "Review deleted successfully"}