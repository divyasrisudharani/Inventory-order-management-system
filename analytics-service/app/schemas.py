from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SalesSummary(BaseModel):
    total_orders: int
    completed_orders: int
    cancelled_orders: int
    total_revenue: float
    average_order_value: float


class ProductSales(BaseModel):
    product_id: int
    product_name: str
    units_sold: int
    revenue: float


class AnalyticsReportResponse(BaseModel):
    id: int
    report_type: str
    report_data: str
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)