from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib.enums import TA_CENTER


def generate_sales_pdf(summary, product_sales):
    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    styles["Title"].alignment = TA_CENTER

    elements = []

    elements.append(
        Paragraph("Inventory and Order Management System", styles["Title"])
    )
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("Sales Summary Report", styles["Heading2"]))
    elements.append(Spacer(1, 10))

    summary_data = [
        ["Metric", "Value"],
        ["Total Orders", str(summary.total_orders)],
        ["Completed Orders", str(summary.completed_orders)],
        ["Cancelled Orders", str(summary.cancelled_orders)],
        ["Total Revenue", f"Rs. {summary.total_revenue:.2f}"],
        ["Average Order Value", f"Rs. {summary.average_order_value:.2f}"],
    ]

    summary_table = Table(summary_data, colWidths=[75 * mm, 75 * mm])

    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#263B5A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))

    elements.append(summary_table)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("Product-wise Sales", styles["Heading2"]))
    elements.append(Spacer(1, 10))

    product_data = [
        ["Product ID", "Product Name", "Units Sold", "Revenue"]
    ]

    for product in product_sales:
        product_data.append([
            str(product.product_id),
            str(product.product_name),
            str(product.units_sold),
            f"Rs. {product.revenue:.2f}",
        ])

    product_table = Table(
        product_data,
        colWidths=[25 * mm, 65 * mm, 30 * mm, 35 * mm],
        repeatRows=1,
    )

    product_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#263B5A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("PADDING", (0, 0), (-1, -1), 7),
    ]))

    elements.append(product_table)

    document.build(elements)

    buffer.seek(0)
    return buffer