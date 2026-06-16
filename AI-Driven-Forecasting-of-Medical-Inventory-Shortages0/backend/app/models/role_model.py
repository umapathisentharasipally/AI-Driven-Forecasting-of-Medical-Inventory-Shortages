from datetime import datetime
from typing import List, Optional, TypedDict

from bson import ObjectId


class RoleDocument(TypedDict):
    _id: ObjectId
    name: str
    permissions: List[str]
    description: Optional[str]
    created_at: datetime