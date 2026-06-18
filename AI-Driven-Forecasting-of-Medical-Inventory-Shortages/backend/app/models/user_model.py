from datetime import datetime
from typing import Optional, TypedDict

from bson import ObjectId


class UserDocument(TypedDict):
    _id: ObjectId
    email: str
    password_hash: str
    full_name: str
    employee_id: Optional[str]
    role_id: ObjectId
    role_name: str
    department: Optional[str]
    is_active: bool
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime