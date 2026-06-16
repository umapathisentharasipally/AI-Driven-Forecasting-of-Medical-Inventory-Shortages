from __future__ import annotations
from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field

class StockReceiptItem(BaseModel):
    inventory_item_id: str
    item_name: str = Field(..., min_length=2, max_length=160)
    quantity: int = Field(..., ge=1)
    batch_no: Optional[str] = Field(default=None, max_length=80)
    expiry_date: Optional[date] = None

class StockReceiptCreate(BaseModel):
    purchase_order_id: Optional[str] = None
    vendor_id: Optional[str] = None
    vendor_name: Optional[str] = Field(default=None, max_length=160)
    received_date: Optional[date] = None
    items: List[StockReceiptItem] = Field(..., min_length=1)

class StockTransferItem(BaseModel):
    inventory_item_id: str
    item_name: str = Field(..., min_length=2, max_length=160)
    quantity: int = Field(..., ge=1)

class StockTransferCreate(BaseModel):
    from_department_id: str
    to_department_id: str
    notes: Optional[str] = Field(default=None, max_length=500)
    items: List[StockTransferItem] = Field(..., min_length=1)
