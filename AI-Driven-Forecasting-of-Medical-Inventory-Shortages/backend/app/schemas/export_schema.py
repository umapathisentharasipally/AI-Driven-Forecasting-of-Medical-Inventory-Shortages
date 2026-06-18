from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ExportType = Literal["inventory", "predictions", "alerts", "anomalies", "audit_logs"]
ExportFormat = Literal["csv", "json"]


class ExportRequest(BaseModel):
    export_type: ExportType
    filters: dict = Field(default_factory=dict)
    format: ExportFormat


class ExportResponse(BaseModel):
    filename: str
    row_count: int
    download_url: str
    created_at: datetime