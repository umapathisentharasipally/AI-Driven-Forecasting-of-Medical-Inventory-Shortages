from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AddressSchema(BaseModel):
    street: str
    city: str
    state: str
    country: str
    pincode: str


class VendorCreate(BaseModel):
    vendor_code: str = Field(..., min_length=2)
    name: str = Field(..., min_length=2)
    contact_email: EmailStr
    contact_phone: Optional[str] = None
    address: Optional[AddressSchema] = None
    avg_lead_time_days: float = Field(..., ge=0)
    reliability_score: float = Field(..., ge=0, le=1)
    contract_expiry: Optional[datetime] = None


class VendorUpdate(BaseModel):
    name: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    address: Optional[AddressSchema] = None
    avg_lead_time_days: Optional[float] = Field(default=None, ge=0)
    reliability_score: Optional[float] = Field(default=None, ge=0, le=1)
    contract_expiry: Optional[datetime] = None
    is_active: Optional[bool] = None


class VendorResponse(BaseModel):
    id: str
    vendor_code: str
    name: str
    contact_email: EmailStr
    contact_phone: Optional[str] = None
    address: Optional[AddressSchema] = None
    avg_lead_time_days: float
    reliability_score: float
    contract_expiry: Optional[datetime] = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(populate_by_name=True)