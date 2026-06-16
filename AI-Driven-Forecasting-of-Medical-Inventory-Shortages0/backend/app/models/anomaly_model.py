from datetime import datetime
from typing import Optional, TypedDict

from bson import ObjectId


class AnomalyDocument(TypedDict):
    _id: ObjectId
    item_id: str
    facility_id: str
    inventory_doc_id: str
    detected_at: datetime
    anomaly_score: float
    is_anomaly: int
    input_snapshot: dict
    is_acknowledged: bool
    acknowledged_by: Optional[str]
    acknowledged_at: Optional[datetime]
    notes: Optional[str]
    created_at: datetime