from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str = Field(..., min_length=2)
    role_id: str
    department: Optional[str] = None
    employee_id: Optional[str] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    department: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    employee_id: Optional[str] = None
    role_id: str
    role_name: str
    department: Optional[str] = None
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(populate_by_name=True)


class UserListResponse(BaseModel):
    items: List[UserResponse]
    total: int
    page: int
    limit: int