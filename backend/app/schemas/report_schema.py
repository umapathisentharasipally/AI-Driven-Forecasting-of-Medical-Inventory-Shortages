from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict


ReportType = Literal[
    "daily_summary",
    "stockout_risk",
    "vendor_performance",
    "anomaly_summary",
]


class ReportGenerateRequest(BaseModel):
    report_type: ReportType
    period_start: datetime
    period_end: datetime


class ReportResponse(BaseModel):
    id: str
    report_type: str
    generated_by: Optional[str] = None
    period_start: datetime
    period_end: datetime
    status: str
    file_path: Optional[str] = None
    summary: Optional[dict] = None
    created_at: datetime

    model_config = ConfigDict(populate_by_name=True)


class ReportListResponse(BaseModel):
    items: List[ReportResponse]
    total: int
    page: int
    limit: int