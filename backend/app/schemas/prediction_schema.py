from datetime import datetime
from typing import List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


RiskLevel = Literal["Low", "Medium", "High", "Critical"]


class RealtimePredictRequest(BaseModel):
    inventory_doc_id: str


class RealtimePredictResponse(BaseModel):
    id: str
    item_id: str
    facility_id: str
    stockout_probability: float = Field(..., ge=0.0, le=1.0)
    stockout_prediction: int = Field(..., ge=0, le=1)
    risk_level: str
    days_of_supply_on_hand: float
    model_name: str
    model_version: str
    prediction_date: datetime
    created_at: datetime

    model_config = ConfigDict(populate_by_name=True)


class BatchPredictRequest(BaseModel):
    facility_id: Optional[str] = None
    item_ids: Optional[List[str]] = None
    run_all: bool = False


class BatchPredictResponse(BaseModel):
    total_items: int
    succeeded: int
    failed: int
    high_risk_count: int
    critical_count: int
    job_id: str = Field(default_factory=lambda: str(uuid4()))


class PredictionListResponse(BaseModel):
    items: List[RealtimePredictResponse]
    total: int
    page: int
    limit: int


class PredictionFilter(BaseModel):
    item_id: Optional[str] = None
    facility_id: Optional[str] = None
    risk_level: Optional[RiskLevel] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1)