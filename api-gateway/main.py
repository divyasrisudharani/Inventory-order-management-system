from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request, Body,Security
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
bearer_scheme = HTTPBearer()
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response


# =========================================================
# 1. MICROSERVICE URLS
# =========================================================

AUTH_URL = "http://127.0.0.1:8001"
PRODUCT_URL = "http://127.0.0.1:8002"
CART_URL = "http://127.0.0.1:8003"
INVENTORY_URL = "http://127.0.0.1:8004"
ORDER_URL = "http://127.0.0.1:8005"
PAYMENT_URL = "http://127.0.0.1:8006"
NOTIFICATION_URL = "http://127.0.0.1:8007"
REVIEW_URL = "http://127.0.0.1:8008"
COUPON_URL = "http://127.0.0.1:8009"
RETURN_URL = "http://127.0.0.1:8010"
ANALYTICS_URL = "http://127.0.0.1:8011"


# =========================================================
# 2. HTTP CLIENT LIFECYCLE
# =========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http_client = httpx.AsyncClient(timeout=30.0)

    yield

    await app.state.http_client.aclose()


# =========================================================
# 3. CREATE API GATEWAY
# =========================================================

app = FastAPI(
    title="Inventory and Order Management API Gateway",
    description=(
        "Central API Gateway for 11 microservices: "
        "Authentication, Products, Cart, Inventory, Orders, "
        "Payments, Notifications, Reviews, Coupons, "
        "Returns and Analytics."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# =========================================================
# 4. CORS FOR REACT FRONTEND
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# 5. COMMON REQUEST FORWARDER
# =========================================================

HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "host",
    "content-length",
    "accept-encoding",
}


async def forward(
    request: Request,
    service_url: str,
    service_path: str,
):
    target_url = (
        service_url.rstrip("/")
        + "/"
        + service_path.lstrip("/")
    )

    if request.url.query:
        target_url += "?" + request.url.query

    body = await request.body()

    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in HOP_BY_HOP_HEADERS
    }

    try:
        client = request.app.state.http_client

        upstream = await client.request(
            method=request.method,
            url=target_url,
            content=body,
            headers=headers,
        )

        excluded_response_headers = {
            "connection",
            "keep-alive",
            "transfer-encoding",
            "content-length",
            "content-encoding",
        }

        response_headers = {
            key: value
            for key, value in upstream.headers.items()
            if key.lower() not in excluded_response_headers
        }

        return Response(
            content=upstream.content,
            status_code=upstream.status_code,
            headers=response_headers,
            media_type=upstream.headers.get("content-type"),
        )

    except httpx.TimeoutException:
        return JSONResponse(
            status_code=504,
            content={
                "detail": "The microservice request timed out."
            },
        )

    except httpx.RequestError:
        return JSONResponse(
            status_code=502,
            content={
                "detail": (
                    "Microservice unavailable. "
                    "Check whether the corresponding service is running."
                )
            },
        )


# =========================================================
# 6. GATEWAY HEALTH
# =========================================================

@app.get("/", tags=["Gateway"])
async def home():
    return {
        "message": (
            "Inventory and Order Management API Gateway is running"
        ),
        "port": 8000,
    }


@app.get("/health", tags=["Gateway"])
async def health():
    return {
        "status": "healthy",
        "service": "api-gateway",
        "port": 8000,
    }


@app.get("/health/services", tags=["Gateway"])
async def service_health(request: Request):
    services = {
        "authentication": AUTH_URL,
        "products": PRODUCT_URL,
        "cart_wishlist": CART_URL,
        "inventory": INVENTORY_URL,
        "orders": ORDER_URL,
        "payments": PAYMENT_URL,
        "notifications": NOTIFICATION_URL,
        "reviews": REVIEW_URL,
        "coupons": COUPON_URL,
        "returns_refunds": RETURN_URL,
        "analytics": ANALYTICS_URL,
    }

    results = {}
    client = request.app.state.http_client

    for name, url in services.items():
        try:
            response = await client.get(
                url + "/health",
                timeout=3.0,
            )

            results[name] = {
                "status": (
                    "healthy"
                    if response.is_success
                    else "unhealthy"
                ),
                "http_status": response.status_code,
            }

        except httpx.RequestError:
            results[name] = {
                "status": "unavailable",
            }

    return {
        "gateway": "healthy",
        "services": results,
    }


# =========================================================
# 7. AUTHENTICATION SERVICE - PORT 8001
# =========================================================

@app.post("/auth/register", tags=["Authentication"])
async def register(
    request: Request,
    body: dict = Body(
        ...,
        example={
            "full_name": "Test Customer",
            "email": "customer@example.com",
            "password": "Customer123!",
        },
    ),
):
    return await forward(
        request, AUTH_URL, "auth/register"
    )


@app.post("/auth/login", tags=["Authentication"])
async def login(
    request: Request,
    body: dict = Body(
        ...,
        example={
            "email": "customer@example.com",
            "password": "Customer123!",
        },
    ),
):
    return await forward(
        request, AUTH_URL, "auth/login"
    )


@app.post("/auth/refresh", tags=["Authentication"])
async def refresh_token(
    request: Request,
    body: dict = Body(
        ...,
        example={
            "refresh_token": "YOUR_REFRESH_TOKEN",
        },
    ),
):
    return await forward(
        request, AUTH_URL, "auth/refresh"
    )


@app.get("/auth/me", tags=["Authentication"])
async def current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
):
    return await forward(
        request,
        AUTH_URL,
        "auth/me",
    )


@app.get("/auth/admin-check", tags=["Authentication"])
async def admin_check(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
):
    return await forward(
        request,
        AUTH_URL,
        "auth/admin-check",
    )


# =========================================================
# 8. PRODUCT SERVICE - PORT 8002
# =========================================================

@app.post("/products", tags=["Products"])
async def create_product(
    request: Request,
    body: dict = Body(
        ...,
        example={
            "name": "Cotton T-Shirt",
            "description": "Comfortable cotton T-shirt",
            "category": "Clothing",
            "brand": "StyleBrand",
            "price": 499.0,
            "image_url": "https://example.com/product.jpg",
        },
    ),
):
    return await forward(
        request, PRODUCT_URL, "products"
    )


@app.get("/products", tags=["Products"])
async def get_products(request: Request):
    return await forward(
        request, PRODUCT_URL, "products"
    )


@app.get("/products/{product_id}", tags=["Products"])
async def get_product(
    product_id: int,
    request: Request,
):
    return await forward(
        request,
        PRODUCT_URL,
        f"products/{product_id}",
    )


@app.put("/products/{product_id}", tags=["Products"])
async def update_product(
    product_id: int,
    request: Request,
    body: dict = Body(
        ...,
        example={
            "name": "Updated Cotton T-Shirt",
            "description": "Updated product description",
            "category": "Clothing",
            "brand": "StyleBrand",
            "price": 549.0,
            "image_url": "https://example.com/updated.jpg",
        },
    ),
):
    return await forward(
        request,
        PRODUCT_URL,
        f"products/{product_id}",
    )


@app.patch("/products/{product_id}", tags=["Products"])
async def patch_product(
    product_id: int,
    request: Request,
    body: dict = Body(
        ...,
        example={
            "price": 549.0,
        },
    ),
):
    return await forward(
        request,
        PRODUCT_URL,
        f"products/{product_id}",
    )


@app.delete("/products/{product_id}", tags=["Products"])
async def delete_product(
    product_id: int,
    request: Request,
):
    return await forward(
        request,
        PRODUCT_URL,
        f"products/{product_id}",
    )


# =========================================================
# 9. CART AND WISHLIST SERVICE - PORT 8003
# =========================================================


@app.post("/cart/", tags=["Cart"], include_in_schema=False)
async def add_to_cart(
    request: Request,credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
    body: dict = Body(
        ...,
        example={
            "product_id": 1,
            "quantity": 2,
        },
    ),
):
    return await forward(
        request, CART_URL, "cart"
    )
@app.post("/cart", tags=["Cart"])
async def add_to_cart(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
    body: dict = Body(
        ...,
        example={
            "product_id": 1,
            "quantity": 2
        }
    ),
):
    return await forward(request, CART_URL, "cart")

@app.get("/cart", tags=["Cart"])
async def get_cart( request: Request,
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
):
    return await forward(
        request,
        CART_URL,
        "cart",
    )

# @app.put("/cart/{item_id}", tags=["Cart"])
# async def update_cart_item(
#     item_id: int,
#     request: Request,credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
#     body: dict = Body(
#         ...,
#         example={
#             "quantity": 3,
#         },
#     ),
# ):
#     return await forward(
#         request,
#         CART_URL,
#         f"cart/{item_id}",
    # )


# @app.patch("/cart/{item_id}", tags=["Cart"])
# async def patch_cart_item(
#     item_id: int,
#     request: Request,
#     body: dict = Body(
#         ...,
#         example={
#             "quantity": 3,
#         },
#     ),
# ):
#     return await forward(
#         request,
#         CART_URL,
#         f"cart/{item_id}",
#     )

@app.put("/cart/items/{product_id}", tags=["Cart"])
async def update_cart_item(
    product_id: int,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
    body: dict = Body(
        ...,
        example={"quantity": 3},
    ),
):
    return await forward(
        request,
        CART_URL,
        f"cart/items/{product_id}",
    )


@app.delete("/cart/items/{product_id}", tags=["Cart"])
async def remove_cart_item(
    product_id: int,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
):
    return await forward(
        request,
        CART_URL,
        f"cart/items/{product_id}",
    )
# @app.delete("/cart/{item_id}", tags=["Cart"])
# async def remove_cart_item(
#     item_id: int,
#     request: Request,credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
# ):
#     return await forward(
#         request,
#         CART_URL,
#         f"cart/{item_id}",
#     )

@app.delete("/cart", tags=["Cart"])
async def clear_cart(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
):
    return await forward(
        request,
        CART_URL,
        "cart",
    )


@app.post("/wishlist", tags=["Wishlist"])
@app.post("/wishlist/", tags=["Wishlist"], include_in_schema=False)
async def add_to_wishlist(
    request: Request,credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
    body: dict = Body(
        ...,
        example={
            "product_id": 1,
        },
    ),
):
    return await forward(
        request, CART_URL, "wishlist"
    )


@app.get("/wishlist", tags=["Wishlist"])
@app.get("/wishlist/", tags=["Wishlist"], include_in_schema=False)
async def get_wishlist(request: Request,credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),):
    return await forward(
        request, CART_URL, "wishlist"
    )


@app.delete("/wishlist/{product_id}", tags=["Wishlist"])
async def remove_from_wishlist(
    product_id: int,
    request: Request,credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
):
    return await forward(
        request,
        CART_URL,
        f"wishlist/{product_id}",
    )


# =========================================================
# 10. INVENTORY SERVICE - PORT 8004
# =========================================================

@app.post("/inventory", tags=["Inventory"])
async def create_inventory(
    request: Request,
    body: dict = Body(
        ...,
        example={
            "product_id": 1,
            "quantity": 20,
            "low_stock_threshold": 5,
        },
    ),
):
    return await forward(
        request, INVENTORY_URL, "inventory"
    )


@app.get("/inventory", tags=["Inventory"])
async def get_inventory(request: Request):
    return await forward(
        request, INVENTORY_URL, "inventory"
    )


@app.get("/inventory/{product_id}", tags=["Inventory"])
async def get_product_inventory(
    product_id: int,
    request: Request,
):
    return await forward(
        request,
        INVENTORY_URL,
        f"inventory/{product_id}",
    )


@app.put("/inventory/{product_id}", tags=["Inventory"])
async def update_inventory(
    product_id: int,
    request: Request,
    body: dict = Body(
        ...,
        example={
            "quantity": 25,
            "low_stock_threshold": 5,
        },
    ),
):
    return await forward(
        request,
        INVENTORY_URL,
        f"inventory/{product_id}",
    )


@app.post("/inventory/reserve", tags=["Inventory"])
async def reserve_stock(
    request: Request,
    body: dict = Body(
        ...,
        example={
            "product_id": 1,
            "order_id": "ORD-1001",
            "quantity": 2,
        },
    ),
):
    return await forward(
        request,
        INVENTORY_URL,
        "inventory/reserve",
    )


@app.post("/inventory/release", tags=["Inventory"])
async def release_stock(
    request: Request,
    body: dict = Body(
        ...,
        example={
            "product_id": 1,
            "order_id": "ORD-1001",
        },
    ),
):
    return await forward(
        request,
        INVENTORY_URL,
        "inventory/release",
    )


# =========================================================
# 11. ORDER SERVICE - PORT 8005
# =========================================================

@app.post("/orders", tags=["Orders"])
async def create_order(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),

    body: dict = Body(
        ...,
        example={
            "shipping_address": "123 Main Road, Hyderabad",
        },
    ),
):
    return await forward(
        request, ORDER_URL, "orders"
    )


@app.get("/orders", tags=["Orders"])
async def get_orders(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
):
    return await forward(
        request, ORDER_URL, "orders"
    )


@app.get("/orders/{order_id}", tags=["Orders"])
async def get_order(
    order_id: int,
    request: Request,credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),

):
    return await forward(
        request,
        ORDER_URL,
        f"orders/{order_id}",
    )


@app.post("/orders/{order_id}/cancel", tags=["Orders"])
async def cancel_order(
    order_id: int,
    request: Request,credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),

):
    return await forward(
        request,
        ORDER_URL,
        f"orders/{order_id}/cancel",
    )


# @app.patch("/orders/{order_id}/status", tags=["Orders"])
# async def update_order_status(
#     order_id: int,
#     request: Request,
#     body: dict = Body(
#         ...,
#         example={
#             "status": "CONFIRMED",
#         },
#     ),
# ):
#     return await forward(
#         request,
#         ORDER_URL,
#         f"orders/{order_id}/status",
#     )


# =========================================================
# 12. PAYMENT SERVICE - PORT 8006
# =========================================================

@app.post("/payments", tags=["Payments"])
async def create_payment(
    request: Request,credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),

    body: dict = Body(
        ...,
        example={
            "order_id": 1,
            "payment_method": "TEST",
        },
    ),
):
    return await forward(
        request, PAYMENT_URL, "payments"
    )


@app.get("/payments", tags=["Payments"])
async def get_payments(request: Request,credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
):
    return await forward(
        request, PAYMENT_URL, "payments"
    )


@app.get("/payments/{payment_id}", tags=["Payments"])
async def get_payment(
    payment_id: int,
    request: Request,credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),

):
    return await forward(
        request,
        PAYMENT_URL,
        f"payments/{payment_id}",
    )


# =========================================================
# 13. NOTIFICATION SERVICE - PORT 8007
# =========================================================

@app.post("/notifications", tags=["Notifications"])
async def create_notification(
    request: Request,credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),

    body: dict = Body(
        ...,
        example={
            "user_id": 1,
            "notification_type": "ORDER",
            "title": "Order Update",
            "message": "Your order has been created.",
            "related_id": "1",
        },
    ),
):
    return await forward(
        request, NOTIFICATION_URL, "notifications/"
    )


@app.get(
    "/notifications/user/{user_id}",
    tags=["Notifications"],
)
async def get_user_notifications(
    user_id: int,
    request: Request,credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),

):
    return await forward(
        request,
        NOTIFICATION_URL,
        f"notifications/user/{user_id}",
    )


# @app.patch(
#     "/notifications/{notification_id}/read",
#     tags=["Notifications"],
# )
# async def mark_notification_read(
#     notification_id: int,
#     request: Request,
# ):
#     return await forward(
#         request,
#         NOTIFICATION_URL,
#         f"notifications/{notification_id}/read",
#     )


@app.delete(
    "/notifications/{notification_id}",
    tags=["Notifications"],
)
async def delete_notification(
    notification_id: int,
    request: Request,credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),

):
    return await forward(
        request,
        NOTIFICATION_URL,
        f"notifications/{notification_id}",
    )


# =========================================================
# 14. REVIEW SERVICE - PORT 8008
# =========================================================

@app.post("/reviews", tags=["Reviews"])
async def create_review(
    request: Request,credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),

    body: dict = Body(
        ...,
        example={
            "product_id": 1,
            "rating": 5,
            "comment": "Good product.",
        },
    ),
):
    return await forward(
        request, REVIEW_URL, "reviews/"
    )


@app.get(
    "/reviews/product/{product_id}",
    tags=["Reviews"],
)
async def get_product_reviews(
    product_id: int,
    request: Request,credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),

):
    return await forward(
        request,
        REVIEW_URL,
        f"reviews/product/{product_id}",
    )


@app.get("/reviews/my", tags=["Reviews"])
async def get_my_reviews(request: Request,credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
):
    return await forward(
        request, REVIEW_URL, "reviews/my"
    )


@app.put("/reviews/{review_id}", tags=["Reviews"])
async def update_review(
    review_id: int,
    request: Request,credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),

    body: dict = Body(
        ...,
        example={
            "rating": 4,
            "comment": "Updated review.",
        },
    ),
):
    return await forward(
        request,
        REVIEW_URL,
        f"reviews/{review_id}",
    )


@app.delete("/reviews/{review_id}", tags=["Reviews"])
async def delete_review(
    review_id: int,
    request: Request,credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),

):
    return await forward(
        request,
        REVIEW_URL,
        f"reviews/{review_id}",
    )


# =========================================================
# 15. COUPON SERVICE - PORT 8009
# =========================================================

@app.post("/coupons", tags=["Coupons"])
async def create_coupon(
    request: Request,
    body: dict = Body(
        ...,
        example={
            "code": "SAVE10",
            "description": "Ten percent discount",
            "discount_type": "PERCENTAGE",
            "discount_value": 10,
            "minimum_order_amount": 500,
            "maximum_discount": 200,
            "usage_limit": 100,
            "is_active": True,
        },
    ),
):
    return await forward(
        request, COUPON_URL, "coupons/"
    )


@app.get("/coupons", tags=["Coupons"])
async def get_coupons(request: Request,credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
):
    return await forward(
        request, COUPON_URL, "coupons/"
    )


@app.post("/coupons/calculate", tags=["Coupons"])
async def calculate_coupon(
    request: Request,
    body: dict = Body(
        ...,
        example={
            "code": "SAVE10",
            "order_amount": 1000,
        },
    ),
):
    return await forward(
        request, COUPON_URL, "coupons/calculate"
    )


@app.patch("/inventory/{product_id}/stock", tags=["Inventory"])
async def adjust_inventory_stock(
    product_id: int,
    request: Request,
    body: dict = Body(
        ...,
        example={
            "quantity_change": 10,
            "transaction_type": "STOCK_IN",
            "reason": "New stock received",
        },
    ),
):
    return await forward(
        request,
        INVENTORY_URL,
        f"inventory/{product_id}/stock",
    )


# =========================================================
# 16. RETURN AND REFUND SERVICE - PORT 8010
# =========================================================

@app.post("/returns", tags=["Returns and Refunds"])
async def create_return(
    request: Request,credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),

    body: dict = Body(
        ...,
        example={
            "order_id": 1,
            "order_item_id": 1,
            "product_id": 1,
            "quantity": 1,
            "reason": "DAMAGED",
            "description": "Product arrived damaged.",
        },
    ),
):
    return await forward(
        request, RETURN_URL, "returns/"
    )


@app.get("/returns/my", tags=["Returns and Refunds"])
async def get_my_returns(request: Request):
    return await forward(
        request, RETURN_URL, "returns/my"
    )


@app.get(
    "/returns/{return_id}",
    tags=["Returns and Refunds"],
)
async def get_return(
    return_id: int,
    request: Request,
):
    return await forward(
        request,
        RETURN_URL,
        f"returns/{return_id}",
    )


@app.patch(
    "/returns/{return_id}/status",
    tags=["Returns and Refunds"],
)
async def update_return_status(
    return_id: int,
    request: Request,
    body: dict = Body(
        ...,
        example={
            "status": "APPROVED",
        },
    ),
):
    return await forward(
        request,
        RETURN_URL,
        f"returns/{return_id}/status",
    )


@app.patch(
    "/returns/{return_id}/refund",
    tags=["Returns and Refunds"],
)
async def update_refund_status(
    return_id: int,
    request: Request,
    body: dict = Body(
        ...,
        example={
            "refund_status": "COMPLETED",
        },
    ),
):
    return await forward(
        request,
        RETURN_URL,
        f"returns/{return_id}/refund",
    )


# =========================================================
# 17. ANALYTICS SERVICE - PORT 8011
# =========================================================

@app.get(
    "/analytics/sales-summary",
    tags=["Analytics"],
)
async def sales_summary(request: Request):
    return await forward(
        request,
        ANALYTICS_URL,
        "analytics/sales-summary",
    )


@app.get(
    "/analytics/product-sales",
    tags=["Analytics"],
)
async def product_sales(request: Request):
    return await forward(
        request,
        ANALYTICS_URL,
        "analytics/product-sales",
    )


@app.post(
    "/analytics/reports",
    tags=["Analytics"],
)
async def create_analytics_report(request: Request):
    return await forward(
        request,
        ANALYTICS_URL,
        "analytics/reports",
    )


@app.get(
    "/analytics/reports",
    tags=["Analytics"],
)
async def get_analytics_reports(request: Request):
    return await forward(
        request,
        ANALYTICS_URL,
        "analytics/reports",
    )
@app.get("/auth/admin/customers", tags=["Authentication"])
async def get_admin_customers(request: Request):
    return await forward(
        request,
        AUTH_URL,
        "auth/admin/customers",
    )