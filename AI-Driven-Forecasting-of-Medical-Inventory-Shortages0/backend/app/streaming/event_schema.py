from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from app.utils.date_utils import utc_now


class KafkaEvent(BaseModel):
    event_id: str
    event_type: str
    source: str = "medical-inventory-api"
    entity: str
    entity_id: Optional[str] = None
    user_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
