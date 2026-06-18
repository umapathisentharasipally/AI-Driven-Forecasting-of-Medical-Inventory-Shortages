from datetime import datetime
from typing import Optional, TypedDict

from bson import ObjectId


class AlertDocument(TypedDict):
    _id: ObjectId
    item_id: str
    facility_id: str
    inventory_doc_id: str
    prediction_id: Optional[str]
    anomaly_id: Optional[str]
    alert_type: str
    severity: str
    message: str
    status: str
    assigned_to: Optional[str]
    snoozed_until: Optional[datetime]
    resolved_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime