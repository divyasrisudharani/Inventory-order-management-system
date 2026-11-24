from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Notification
from app.schemas import NotificationCreate, NotificationResponse

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


@router.post("/", response_model=NotificationResponse, status_code=201)
def create_notification(
    payload: NotificationCreate,
    db: Session = Depends(get_db),
):
    notification = Notification(
        user_id=payload.user_id,
        notification_type=payload.notification_type,
        title=payload.title,
        message=payload.message,
        related_id=payload.related_id,
    )

    db.add(notification)
    db.commit()
    db.refresh(notification)

    return notification


@router.get("/user/{user_id}", response_model=list[NotificationResponse])
def get_user_notifications(
    user_id: int,
    db: Session = Depends(get_db),
):
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .all()
    )


@router.patch("/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
):
    notification = db.query(Notification).filter(
        Notification.id == notification_id
    ).first()

    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Notification not found",
        )

    notification.status = "READ"
    db.commit()

    return {
        "message": "Notification marked as read",
        "notification_id": notification_id,
    }


@router.delete("/{notification_id}")
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
):
    notification = db.query(Notification).filter(
        Notification.id == notification_id
    ).first()

    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Notification not found",
        )

    db.delete(notification)
    db.commit()

    return {"message": "Notification deleted successfully"}