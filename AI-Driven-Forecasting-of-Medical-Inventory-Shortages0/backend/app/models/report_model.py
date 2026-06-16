from datetime import datetime
from typing import Optional, TypedDict

from bson import ObjectId


class ReportDocument(TypedDict):
    _id: ObjectId
    report_type: str
    generated_by: Optional[str]
    period_start: datetime
    period_end: datetime
    status: str
    file_path: Optional[str]
    summary: Optional[dict]
    created_at: datetime