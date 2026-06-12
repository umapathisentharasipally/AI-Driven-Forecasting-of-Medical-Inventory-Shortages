from datetime import datetime
from typing import Optional, TypedDict

from bson import ObjectId


class NotificationDocument(TypedDict):
    _id: ObjectId
    user_id: str
    alert_id: Optional[str]
    channel: str
    title: str
    body: str
    is_read: bool
    sent_at: Optional[datetime]
    created_at: datetime