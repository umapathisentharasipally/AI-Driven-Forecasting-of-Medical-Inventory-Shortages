from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field

class DepartmentCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    code: str = Field(..., min_length=2, max_length=40)
    facility_id: Optional[str] = None
    manager_name: Optional[str] = Field(default=None, max_length=120)
    is_active: bool = True

class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    facility_id: Optional[str] = None
    manager_name: Optional[str] = Field(default=None, max_length=120)
    is_active: Optional[bool] = None
