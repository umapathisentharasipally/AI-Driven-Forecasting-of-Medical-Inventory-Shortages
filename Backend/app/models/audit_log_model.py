from datetime import datetime
from typing import Optional, TypedDict

from bson import ObjectId


class AuditLogDocument(TypedDict):
    _id: ObjectId
    user_id: Optional[str]
    action: str
    resource_type: str
    resource_id: Optional[str]
    changes: Optional[dict]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime