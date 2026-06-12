from datetime import datetime
from typing import List, Literal, TypedDict

from bson import ObjectId


ForecastPeriod = Literal["daily", "weekly", "monthly"]


class TrendDocument(TypedDict):
    _id: ObjectId
    item_id: str
    facility_id: str
    period: ForecastPeriod
    forecast_periods: int
    forecast_rows: List[dict]
    computed_at: datetime
    config_used: dict