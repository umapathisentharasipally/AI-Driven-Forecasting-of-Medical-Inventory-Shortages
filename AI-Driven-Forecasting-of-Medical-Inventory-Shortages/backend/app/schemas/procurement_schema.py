from __future__ import annotations
from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field

class PurchaseOrderItem(BaseModel):
    inventory_item_id: Optional[str] = None
    item_name: str = Field(..., min_length=2, max_length=160)
    quantity: int = Field(..., ge=1)
    unit_price: float = Field(default=0, ge=0)

class PurchaseOrderCreate(BaseModel):
    vendor_id: Optional[str] = None
    vendor_name: str = Field(..., min_length=2, max_length=160)
    expected_date: Optional[date] = None
    notes: Optional[str] = Field(default=None, max_length=500)
    items: List[PurchaseOrderItem] = Field(..., min_length=1)

class PurchaseOrderUpdate(BaseModel):
    vendor_id: Optional[str] = None
    vendor_name: Optional[str] = Field(default=None, min_length=2, max_length=160)
    expected_date: Optional[date] = None
    notes: Optional[str] = Field(default=None, max_length=500)
