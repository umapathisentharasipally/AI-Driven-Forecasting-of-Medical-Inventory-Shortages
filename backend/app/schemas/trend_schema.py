from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


TrendPeriod = Literal["daily", "weekly", "monthly"]


class TrendComputeRequest(BaseModel):
    item_id: Optional[str] = None
    facility_id: Optional[str] = None
    period: TrendPeriod


class ForecastRow(BaseModel):
    ds: datetime
    yhat: float
    yhat_lower: float
    yhat_upper: float


class TrendResponse(BaseModel):
    id: str
    item_id: Optional[str] = None
    facility_id: Optional[str] = None
    period: TrendPeriod
    forecast_periods: int
    forecast_rows: List[ForecastRow]
    computed_at: datetime
    config_used: dict

    model_config = ConfigDict(populate_by_name=True)


class TrendListResponse(BaseModel):
    items: List[TrendResponse]
    total: int
    page: int
    limit: int