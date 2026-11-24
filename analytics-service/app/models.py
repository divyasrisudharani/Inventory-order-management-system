from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Float, DateTime, Text

from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class AnalyticsReport(Base):
    __tablename__ = "analytics_reports"

    id = Column(Integer, primary_key=True, index=True)
    report_type = Column(String(50), nullable=False, index=True)
    report_data = Column(Text, nullable=False)
    generated_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    