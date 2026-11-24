from datetime import datetime
from decimal import Decimal
from typing import Optional

import httpx

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Cart, Wishlist
from app.schemas import (
    CartCreate,
    CartUpdate,
    CartResponse,
    WishlistCreate,
    WishlistResponse,
    CartSummary,
    CartItemSummary,
)


router = APIRouter(tags=["Cart and Wishlist"])

# --------------------------------------------------
# MICROSERVICE URLS
# --------------------------------------------------

AUTH_SERVICE_URL = "http://127.0.0.1:8001"
PRODUCT_SERVICE_URL = "http://127.0.0.1:8002"

# --------------------------------------------------
# AUTHENTICATION
# --------------------------------------------------

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        bearer_scheme
    ),
):
    """
    Validate the access token through Auth Service.

    Expected header:
    Authorization: Bearer <access_token>
    """

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        response = httpx.get(
            f"{AUTH_SERVICE_URL}/auth/me",
            headers={
                "Authorization": f"Bearer {credentials.credentials}"
            },
            timeout=5.0,
        )

        if response.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired access token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        response.raise_for_status()

        user = response.json()

        if not user.get("id"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user information",
            )

        return user

    except HTTPException:
        raise

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Authentication Service timed out",
        )

    except httpx.HTTPStatusError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Authentication Service returned an error",
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication Service is unavailable",
        )


# --------------------------------------------------
# PRODUCT SERVICE INTEGRATION
# --------------------------------------------------

def get_product(product_id: int) -> dict:
    """
    Retrieve product information from Product Service.
    """

    try:
        response = httpx.get(
            f"{PRODUCT_SERVICE_URL}/products/{product_id}",
            timeout=5.0,
        )

        if response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} not found",
            )

        response.raise_for_status()

        product = response.json()

        if product.get("is_active") is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This product is not available",
            )

        return product

    except HTTPException:
        raise

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Product Service timed out",
        )

    except httpx.HTTPStatusError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Product Service returned an error",
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Product Service is unavailable",
        )


# --------------------------------------------------
# CART: ADD ITEM
# --------------------------------------------------

@router.post(
    "/cart",
    response_model=CartResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_to_cart(
    item: CartCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id = int(current_user["id"])

    # Verify the product exists.
    get_product(item.product_id)

    cart_item = (
        db.query(Cart)
        .filter(
            Cart.user_id == user_id,
            Cart.product_id == item.product_id,
        )
        .first()
    )

    if cart_item:
        cart_item.quantity += item.quantity
        cart_item.updated_at = datetime.utcnow()
    else:
        cart_item = Cart(
            user_id=user_id,
            product_id=item.product_id,
            quantity=item.quantity,
        )
        db.add(cart_item)

    try:
        db.commit()
        db.refresh(cart_item)
        return cart_item

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Could not add this product to the cart",
        )


# --------------------------------------------------
# CART: VIEW CART
# --------------------------------------------------

@router.get("/cart", response_model=CartSummary)
def get_cart(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id = int(current_user["id"])

    cart_items = (
        db.query(Cart)
        .filter(Cart.user_id == user_id)
        .all()
    )

    result_items = []
    total_items = 0
    total_amount = Decimal("0.00")

    for item in cart_items:
        product = get_product(item.product_id)

        price = Decimal(str(product["price"]))
        subtotal = price * item.quantity

        result_items.append(
            CartItemSummary(
                product_id=item.product_id,
                product_name=product["name"],
                price=float(price),
                quantity=item.quantity,
                subtotal=float(subtotal),
            )
        )

        total_items += item.quantity
        total_amount += subtotal

    return CartSummary(
        items=result_items,
        total_items=total_items,
        total_amount=float(total_amount),
    )


# --------------------------------------------------
# CART: UPDATE QUANTITY
# --------------------------------------------------

@router.put(
    "/cart/items/{product_id}",
    response_model=CartResponse,
)
def update_cart_item(
    product_id: int,
    item: CartUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id = int(current_user["id"])

    get_product(product_id)

    cart_item = (
        db.query(Cart)
        .filter(
            Cart.user_id == user_id,
            Cart.product_id == product_id,
        )
        .first()
    )

    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found in your cart",
        )

    cart_item.quantity = item.quantity
    cart_item.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(cart_item)

    return cart_item


# --------------------------------------------------
# CART: REMOVE ITEM
# --------------------------------------------------

@router.delete("/cart/items/{product_id}")
def remove_cart_item(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id = int(current_user["id"])

    cart_item = (
        db.query(Cart)
        .filter(
            Cart.user_id == user_id,
            Cart.product_id == product_id,
        )
        .first()
    )

    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found in your cart",
        )

    db.delete(cart_item)
    db.commit()

    return {"message": "Item removed from cart"}


# --------------------------------------------------
# CART: CLEAR CART
# --------------------------------------------------

@router.delete("/cart")
def clear_cart(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id = int(current_user["id"])

    db.query(Cart).filter(
        Cart.user_id == user_id
    ).delete(synchronize_session=False)

    db.commit()

    return {"message": "Your cart has been cleared"}


# --------------------------------------------------
# WISHLIST: ADD PRODUCT
# --------------------------------------------------

@router.post(
    "/wishlist",
    response_model=WishlistResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_to_wishlist(
    item: WishlistCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id = int(current_user["id"])

    get_product(item.product_id)

    existing_item = (
        db.query(Wishlist)
        .filter(
            Wishlist.user_id == user_id,
            Wishlist.product_id == item.product_id,
        )
        .first()
    )

    if existing_item:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product is already in your wishlist",
        )

    wishlist_item = Wishlist(
        user_id=user_id,
        product_id=item.product_id,
    )

    db.add(wishlist_item)

    try:
        db.commit()
        db.refresh(wishlist_item)
        return wishlist_item

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product is already in your wishlist",
        )


# --------------------------------------------------
# WISHLIST: VIEW WISHLIST
# --------------------------------------------------

@router.get(
    "/wishlist",
    response_model=list[WishlistResponse],
)
def get_wishlist(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id = int(current_user["id"])

    return (
        db.query(Wishlist)
        .filter(Wishlist.user_id == user_id)
        .all()
    )


# --------------------------------------------------
# WISHLIST: REMOVE PRODUCT
# --------------------------------------------------

@router.delete("/wishlist/{product_id}")
def remove_from_wishlist(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id = int(current_user["id"])

    wishlist_item = (
        db.query(Wishlist)
        .filter(
            Wishlist.user_id == user_id,
            Wishlist.product_id == product_id,
        )
        .first()
    )

    if not wishlist_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found in your wishlist",
        )

    db.delete(wishlist_item)
    db.commit()

    return {"message": "Product removed from wishlist"}