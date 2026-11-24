from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import asc, desc, or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Product
from app.schemas import ProductCreate, ProductUpdate, ProductResponse
import json
from fastapi.encoders import jsonable_encoder
from app.redis_client import redis_client

router = APIRouter(prefix="/products", tags=["Products"])


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
):
    product_data = data.model_dump()

    if product_data.get("image_url") is not None:
        product_data["image_url"] = str(product_data["image_url"])

    product = Product(**product_data)

    db.add(product)
    db.commit()
    db.refresh(product)

    return product


@router.get("", response_model=list[ProductResponse])
def get_products(
    search: str | None = None,
    category: str | None = None,
    min_price: float | None = Query(default=None, ge=0),
    max_price: float | None = Query(default=None, ge=0),
    sort_by: str = Query(default="created_at"),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    # Create a unique Redis cache key for these filters
    cache_key = (
        f"products:{search}:{category}:{min_price}:"
        f"{max_price}:{sort_by}:{order}:{page}:{limit}"
    )

    # Check Redis cache
    try:
        cached_products = redis_client.get(cache_key)

        if cached_products:
            print("Products fetched from Redis cache")
            return json.loads(cached_products)

    except Exception as e:
        print("Redis cache read failed:", e)

    # Fetch products from SQLite
    query = db.query(Product).filter(Product.is_active.is_(True))

    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Product.name.ilike(term),
                Product.description.ilike(term),
                Product.brand.ilike(term),
            )
        )

    if category:
        query = query.filter(
            Product.category.ilike(category.strip())
        )

    if min_price is not None:
        query = query.filter(Product.price >= min_price)

    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    if (
        min_price is not None
        and max_price is not None
        and min_price > max_price
    ):
        raise HTTPException(
            status_code=400,
            detail="min_price cannot exceed max_price",
        )

    allowed_sort_fields = {
        "name": Product.name,
        "price": Product.price,
        "created_at": Product.created_at,
        "rating": Product.rating,
    }

    if sort_by not in allowed_sort_fields:
        raise HTTPException(
            status_code=400,
            detail="Invalid sort_by field",
        )

    sort_column = allowed_sort_fields[sort_by]

    query = query.order_by(
        asc(sort_column) if order == "asc"
        else desc(sort_column)
    )

    offset = (page - 1) * limit

    products = query.offset(offset).limit(limit).all()

    # Convert SQLAlchemy objects into JSON-compatible data
    products_data = jsonable_encoder(products)

    # Store products in Redis for 60 seconds
    try:
        redis_client.set(
            cache_key,
            json.dumps(products_data),
            ex=60,
        )
        print("Products stored in Redis cache")

    except Exception as e:
        print("Redis cache write failed:", e)

    return products_data

@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    product = (
        db.query(Product)
        .filter(
            Product.id == product_id,
            Product.is_active.is_(True),
        )
        .first()
    )

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    return product


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    data: ProductUpdate,
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.is_active.is_(True),
    ).first()

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    update_data = data.model_dump(exclude_unset=True)

    if "image_url" in update_data:
        image_url = update_data["image_url"]
        update_data["image_url"] = (
            str(image_url) if image_url is not None else None
        )

    for field, value in update_data.items():
        if value is None:
            raise HTTPException(
                status_code=422,
                detail=f"{field} cannot be null",
            )

        setattr(product, field, value)

    db.commit()
    db.refresh(product)

    return product

@router.patch("/products/{product_id}")
def patch_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    update_data = product_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)

    return product

@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.is_active.is_(True),
    ).first()

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    # Soft deletion preserves product history for related services.
    product.is_active = False

    db.commit()

    return {
        "message": "Product deactivated successfully",
        "product_id": product_id,
    }