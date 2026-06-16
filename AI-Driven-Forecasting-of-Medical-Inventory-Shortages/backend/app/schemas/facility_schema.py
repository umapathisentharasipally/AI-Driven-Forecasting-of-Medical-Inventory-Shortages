from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field

class FacilityCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    code: str = Field(..., min_length=2, max_length=40)
    facility_type: str = Field(default="hospital", max_length=60)
    address: Optional[str] = Field(default=None, max_length=300)
    city: Optional[str] = Field(default=None, max_length=80)
    state: Optional[str] = Field(default=None, max_length=80)
    is_active: bool = True

class FacilityUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    facility_type: Optional[str] = Field(default=None, max_length=60)
    address: Optional[str] = Field(default=None, max_length=300)
    city: Optional[str] = Field(default=None, max_length=80)
    state: Optional[str] = Field(default=None, max_length=80)
    is_active: Optional[bool] = None
