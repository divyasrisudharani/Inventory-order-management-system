import json
import httpx
from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
bearer_scheme = HTTPBearer()
from app.database import get_db
from app.models import AnalyticsReport
from fastapi.responses import StreamingResponse
from app.pdf_generator import generate_sales_pdf
from app.schemas import (
    SalesSummary,
    ProductSales,
    AnalyticsReportResponse,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])

AUTH_SERVICE_URL = "http://127.0.0.1:8001"
ORDER_SERVICE_URL = "http://127.0.0.1:8005"


def get_admin_user(authorization: str = Header(...)):
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

    if user.get("role") != "administrator":
        raise HTTPException(status_code=403, detail="Administrator access required")

    return user


def fetch_orders(authorization: str):
    try:
        response = httpx.get(
            f"{ORDER_SERVICE_URL}/orders",
            headers={"Authorization": authorization},
            timeout=15.0,
        )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Order Service unavailable")

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail="Could not retrieve orders from Order Service",
        )

    data = response.json()

    # Supports either a list or {"orders": [...]} response.
    if isinstance(data, list):
        return data

    if isinstance(data, dict) and isinstance(data.get("orders"), list):
        return data["orders"]

    raise HTTPException(status_code=502, detail="Unexpected Order Service response")


@router.get("/sales-summary", response_model=SalesSummary)
def sales_summary(
    credentials:HTTPAuthorizationCredentials = Depends(bearer_scheme),
    user: dict = Depends(get_admin_user),
):
    authorization = f"Bearer {credentials.credentials}"
    orders = fetch_orders(authorization)

    completed = [
        order for order in orders
        if order.get("status") in {"CONFIRMED","DELIVERED", "COMPLETED"}
    ]
    cancelled = [
        order for order in orders
        if order.get("status") == "CANCELLED"
    ]

    revenue = sum(float(order.get("total_amount", 0)) for order in completed)
    average = revenue / len(completed) if completed else 0.0

    return SalesSummary(
        total_orders=len(orders),
        completed_orders=len(completed),
        cancelled_orders=len(cancelled),
        total_revenue=round(revenue, 2),
        average_order_value=round(average, 2),
    )


@router.get("/product-sales", response_model=list[ProductSales])
def product_sales(
    authorization: str = Header(...),
    user: dict = Depends(get_admin_user),
):
    orders = fetch_orders(authorization)
    results = {}

    for order in orders:
        if order.get("status") not in {"CONFIRMED","DELIVERED", "COMPLETED"}:
            continue

        for item in order.get("items", []):
            product_id = int(item.get("product_id", 0))
            if product_id <= 0:
                continue

            if product_id not in results:
                results[product_id] = {
                    "product_id": product_id,
                    "product_name": item.get("product_name", "Unknown product"),
                    "units_sold": 0,
                    "revenue": 0.0,
                }

            results[product_id]["units_sold"] += int(item.get("quantity", 0))
            results[product_id]["revenue"] += float(item.get("subtotal", 0))

    return [
        ProductSales(**{
            **item,
            "revenue": round(item["revenue"], 2),
        })
        for item in results.values()
    ]


@router.post("/reports", response_model=AnalyticsReportResponse, status_code=201)
def save_sales_report(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    user: dict = Depends(get_admin_user),
    db=Depends(get_db),
):
    authorization = f"Bearer {credentials.credentials}"

    orders = fetch_orders(authorization)

    completed = [
        order for order in orders
        if order.get("status") in {"CONFIRMED","DELIVERED", "COMPLETED"}
    ]

    cancelled = [
        order for order in orders
        if order.get("status") == "CANCELLED"
    ]

    revenue = sum(float(order.get("total_amount", 0)) for order in completed)
    average = revenue / len(completed) if completed else 0.0

    summary = SalesSummary(
        total_orders=len(orders),
        completed_orders=len(completed),
        cancelled_orders=len(cancelled),
        total_revenue=round(revenue, 2),
        average_order_value=round(average, 2),
    )

    report = AnalyticsReport(
        report_type="SALES_SUMMARY",
        report_data=json.dumps(summary.model_dump()),
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    return report

@router.get("/reports", response_model=list[AnalyticsReportResponse])
def list_reports(
    user: dict = Depends(get_admin_user),
    db=Depends(get_db),
):
    return (
        db.query(AnalyticsReport)
        .order_by(AnalyticsReport.generated_at.desc())
        .all()
    )
@router.get("/reports/pdf")
def download_sales_pdf(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    user: dict = Depends(get_admin_user),
):
    authorization = f"Bearer {credentials.credentials}"

    orders = fetch_orders(authorization)

    completed = [
        order for order in orders
        if order.get("status") in {"CONFIRMED","DELIVERED", "COMPLETED"}
    ]

    cancelled = [
        order for order in orders
        if order.get("status") == "CANCELLED"
    ]

    revenue = sum(float(order.get("total_amount", 0)) for order in completed)
    average = revenue / len(completed) if completed else 0.0

    summary = SalesSummary(
        total_orders=len(orders),
        completed_orders=len(completed),
        cancelled_orders=len(cancelled),
        total_revenue=round(revenue, 2),
        average_order_value=round(average, 2),
    )

    products = product_sales(
        authorization=authorization,
        user=user,
    )

    pdf_buffer = generate_sales_pdf(summary, products)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="sales_report.pdf"'
        },
    )