from datetime import datetime
from typing import List, Optional, TypedDict

from bson import ObjectId


class InventoryItemDocument(TypedDict):
    _id: ObjectId
    item_id: str
    facility_id: str
    item_name: str
    category: str
    unit_of_measure: str
    current_stock_on_hand: float
    safety_stock_level: float
    days_of_supply_on_hand: float
    avg_daily_usage_last_30d: float
    avg_daily_usage_last_90d: float
    usage_cv_last_90d: float
    stock_as_pct_of_safety_level: float
    reorder_point: float
    reorder_quantity: float
    vendor_id: ObjectId
    vendor_reliability_score: float
    actual_avg_lead_time_last_6m: float
    lead_time_variability_days: float
    backorder_frequency_last_12m: float
    expiry_date: Optional[datetime]
    department_tags: List[str]
    is_critical: bool
    is_active: bool
    last_restocked_at: Optional[datetime]
    snapshot_date: datetime
    created_at: datetime
    updated_at: datetime