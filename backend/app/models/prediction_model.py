from datetime import datetime
from typing import TypedDict

from bson import ObjectId


class PredictionDocument(TypedDict):
    _id: ObjectId
    item_id: str
    facility_id: str
    inventory_doc_id: str
    model_name: str
    model_version: str
    prediction_date: datetime
    stockout_probability: float
    stockout_prediction: int
    risk_level: str
    days_of_supply_on_hand: float
    feature_snapshot: dict
    created_at: datetime