from datetime import datetime
from typing import Optional, TypedDict

from bson import ObjectId


class VendorDocument(TypedDict):
    _id: ObjectId
    vendor_code: str
    name: str
    contact_email: str
    contact_phone: Optional[str]
    address: Optional[dict]
    avg_lead_time_days: float
    reliability_score: float
    contract_expiry: Optional[datetime]
    is_active: bool
    created_at: datetime