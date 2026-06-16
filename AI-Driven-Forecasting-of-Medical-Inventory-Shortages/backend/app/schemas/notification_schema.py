from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


NotificationChannel = Literal["in_app", "email", "sms"]


class NotificationResponse(BaseModel):
    id: str
    user_id: str
    alert_id: Optional[str] = None
    channel: NotificationChannel
    title: str
    body: str
    is_read: bool
    sent_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(populate_by_name=True)


class NotificationListResponse(BaseModel):
    items: List[NotificationResponse]
    total: int
    page: int
    limit: int


class MarkReadRequest(BaseModel):
    notification_ids: List[str] = Field(..., min_length=1)