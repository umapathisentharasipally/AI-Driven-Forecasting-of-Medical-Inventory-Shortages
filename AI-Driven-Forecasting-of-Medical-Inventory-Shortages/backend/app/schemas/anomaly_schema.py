from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class AnomalyResponse(BaseModel):
    id: str
    item_id: str
    facility_id: str
    inventory_doc_id: str
    detected_at: datetime
    anomaly_score: float
    is_anomaly: int = Field(..., ge=0, le=1)
    input_snapshot: dict
    is_acknowledged: bool
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(populate_by_name=True)


class AnomalyListResponse(BaseModel):
    items: List[AnomalyResponse]
    total: int
    page: int
    limit: int


class AnomalyAcknowledgeRequest(BaseModel):
    notes: Optional[str] = None


class AnomalyFilter(BaseModel):
    item_id: Optional[str] = None
    facility_id: Optional[str] = None
    is_anomaly: Optional[int] = Field(default=None, ge=0, le=1)
    is_acknowledged: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1)