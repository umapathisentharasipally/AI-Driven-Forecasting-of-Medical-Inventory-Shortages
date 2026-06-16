from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field

class PrescriptionItem(BaseModel):
    inventory_item_id: str
    medicine_name: str = Field(..., min_length=2, max_length=160)
    quantity: int = Field(..., ge=1)

class PrescriptionCreate(BaseModel):
    patient_name: str = Field(..., min_length=2, max_length=120)
    patient_ref: Optional[str] = Field(default=None, max_length=80)
    doctor_name: Optional[str] = Field(default=None, max_length=120)
    items: List[PrescriptionItem] = Field(..., min_length=1)

class ReturnCreate(BaseModel):
    prescription_id: Optional[str] = None
    inventory_item_id: str
    medicine_name: str = Field(..., min_length=2, max_length=160)
    quantity: int = Field(..., ge=1)
    reason: str = Field(..., min_length=2, max_length=300)
