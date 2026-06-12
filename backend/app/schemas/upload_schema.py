from datetime import datetime
from typing import List

from pydantic import BaseModel


class UploadResponse(BaseModel):
    filename: str
    rows_processed: int
    rows_failed: int
    errors: List[str]
    created_at: datetime