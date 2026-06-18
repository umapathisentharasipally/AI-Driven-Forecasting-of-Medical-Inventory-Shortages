from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


InventoryCategory = Literal["PPE", "Medication", "Surgical", "Lab", "Other"]


class InventoryItemCreate(BaseModel):
    item_id: str = Field(..., min_length=1)
    facility_id: str = Field(..., min_length=1)
    item_name: str = Field(..., min_length=2)
    category: InventoryCategory
    unit_of_measure: str = Field(..., min_length=1)

    current_stock_on_hand: float = Field(..., ge=0)
    safety_stock_level: float = Field(..., gt=0)
    avg_daily_usage_last_30d: float = Field(..., ge=0)
    avg_daily_usage_last_90d: float = Field(..., ge=0)
    usage_cv_last_90d: float = Field(..., ge=0)

    reorder_point: float = Field(..., ge=0)
    reorder_quantity: float = Field(..., ge=0)

    vendor_id: str
    vendor_reliability_score: float = Field(..., ge=0, le=1)
    actual_avg_lead_time_last_6m: float = Field(..., ge=0)
    lead_time_variability_days: float = Field(..., ge=0)
    backorder_frequency_last_12m: float = Field(..., ge=0)

    expiry_date: Optional[datetime] = None
    department_tags: List[str] = Field(default_factory=list)
    is_critical: bool = False
    is_active: bool = True
    last_restocked_at: Optional[datetime] = None

    @field_validator("department_tags")
    @classmethod
    def clean_department_tags(cls, value: List[str]) -> List[str]:
        return [tag.strip() for tag in value if tag and tag.strip()]


class InventoryItemUpdate(BaseModel):
    item_name: Optional[str] = None
    category: Optional[InventoryCategory] = None
    unit_of_measure: Optional[str] = None

    current_stock_on_hand: Optional[float] = Field(default=None, ge=0)
    safety_stock_level: Optional[float] = Field(default=None, gt=0)
    avg_daily_usage_last_30d: Optional[float] = Field(default=None, ge=0)
    avg_daily_usage_last_90d: Optional[float] = Field(default=None, ge=0)
    usage_cv_last_90d: Optional[float] = Field(default=None, ge=0)

    reorder_point: Optional[float] = Field(default=None, ge=0)
    reorder_quantity: Optional[float] = Field(default=None, ge=0)

    vendor_id: Optional[str] = None
    vendor_reliability_score: Optional[float] = Field(default=None, ge=0, le=1)
    actual_avg_lead_time_last_6m: Optional[float] = Field(default=None, ge=0)
    lead_time_variability_days: Optional[float] = Field(default=None, ge=0)
    backorder_frequency_last_12m: Optional[float] = Field(default=None, ge=0)

    expiry_date: Optional[datetime] = None
    department_tags: Optional[List[str]] = None
    is_critical: Optional[bool] = None
    is_active: Optional[bool] = None
    last_restocked_at: Optional[datetime] = None


class InventoryItemResponse(BaseModel):
    id: str
    item_id: str
    facility_id: str
    item_name: str
    category: str
    unit_of_measure: str

    current_stock_on_hand: float
    safety_stock_level: float
    days_of_supply_on_hand: float
    avg_daily_usage_last_30d: float
    avg_daily_usage_last_90d: float
    usage_cv_last_90d: float
    stock_as_pct_of_safety_level: float

    reorder_point: float
    reorder_quantity: float

    vendor_id: str
    vendor_reliability_score: float
    actual_avg_lead_time_last_6m: float
    lead_time_variability_days: float
    backorder_frequency_last_12m: float

    expiry_date: Optional[datetime] = None
    department_tags: List[str]
    is_critical: bool
    is_active: bool
    last_restocked_at: Optional[datetime] = None
    snapshot_date: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(populate_by_name=True)


class StockAdjustRequest(BaseModel):
    delta: float
    reason: str = Field(..., min_length=3)
    adjustment_type: Literal["usage", "restock", "correction", "waste"]

    @field_validator("delta")
    @classmethod
    def delta_must_be_nonzero(cls, value: float) -> float:
        if value == 0:
            raise ValueError("delta must be nonzero")
        return value


class InventoryListResponse(BaseModel):
    items: List[InventoryItemResponse]
    total: int
    page: int
    limit: int


class InventoryFilter(BaseModel):
    category: Optional[InventoryCategory] = None
    facility_id: Optional[str] = None
    department: Optional[str] = None
    is_critical: Optional[bool] = None
    is_active: Optional[bool] = None
    below_safety_stock: Optional[bool] = None
    vendor_id: Optional[str] = None
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1)