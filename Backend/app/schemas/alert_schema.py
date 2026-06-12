from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


AlertType = Literal["stockout_risk", "below_safety", "expiry", "anomaly"]
AlertSeverity = Literal["Critical", "High", "Medium", "Low"]
AlertStatus = Literal["open", "acknowledged", "resolved", "snoozed"]


class AlertResponse(BaseModel):
    id: str
    item_id: str
    facility_id: str
    inventory_doc_id: str
    prediction_id: Optional[str] = None
    anomaly_id: Optional[str] = None
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    status: AlertStatus
    assigned_to: Optional[str] = None
    snoozed_until: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(populate_by_name=True)


class AlertListResponse(BaseModel):
    items: List[AlertResponse]
    total: int
    page: int
    limit: int


class AlertStatusUpdate(BaseModel):
    status: AlertStatus
    resolved_at: Optional[datetime] = None
    snoozed_until: Optional[datetime] = None

    @model_validator(mode="after")
    def validate_snooze(self):
        if self.status == "snoozed" and self.snoozed_until is None:
            raise ValueError("snoozed_until is required when status is snoozed")
        return self


class AlertAssignRequest(BaseModel):
    user_id: str = Field(..., min_length=1)


class AlertFilter(BaseModel):
    status: Optional[AlertStatus] = None
    severity: Optional[AlertSeverity] = None
    alert_type: Optional[AlertType] = None
    item_id: Optional[str] = None
    facility_id: Optional[str] = None
    assigned_to: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1)


class AlertDashboardCounts(BaseModel):
    critical: int
    high: int
    medium: int
    low: int
    open_total: int
    resolved_today: int
    snoozed: int