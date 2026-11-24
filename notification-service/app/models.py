from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, Text, Index

from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    notification_type = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="UNREAD")
    related_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        Index("ix_notifications_user_created", "user_id", "created_at"),
    )