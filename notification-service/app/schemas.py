from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class NotificationCreate(BaseModel):
    user_id: int = Field(..., gt=0)
    notification_type: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1)
    related_id: int | None = Field(default=None, gt=0)


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    notification_type: str
    title: str
    message: str
    status: str
    related_id: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)