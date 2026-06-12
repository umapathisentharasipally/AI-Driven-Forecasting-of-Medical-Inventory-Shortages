from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class RoleCreate(BaseModel):
    name: str = Field(..., min_length=2)
    permissions: List[str] = Field(..., min_length=1)
    description: Optional[str] = None


class RoleUpdate(BaseModel):
    permissions: Optional[List[str]] = None
    description: Optional[str] = None


class RoleResponse(BaseModel):
    id: str
    name: str
    permissions: List[str]
    description: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(populate_by_name=True)