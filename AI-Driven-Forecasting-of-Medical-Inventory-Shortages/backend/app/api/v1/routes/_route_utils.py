from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from fastapi import Query

from app.core.exception_handler import ValidationException


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def validate_object_id(value: str, field_name: str = "id") -> ObjectId:
    if not ObjectId.is_valid(value):
        raise ValidationException(f"Invalid {field_name}", details={field_name: value})
    return ObjectId(value)


def serialize_doc(doc: dict[str, Any] | None) -> dict[str, Any] | None:
    if doc is None:
        return None
    out: dict[str, Any] = {}
    for key, value in doc.items():
        if key == "_id":
            out["id"] = str(value)
        elif isinstance(value, ObjectId):
            out[key] = str(value)
        elif isinstance(value, datetime):
            out[key] = value.isoformat()
        elif isinstance(value, list):
            out[key] = [serialize_value(item) for item in value]
        elif isinstance(value, dict):
            out[key] = {k: serialize_value(v) for k, v in value.items()}
        else:
            out[key] = value
    return out


def serialize_value(value: Any) -> Any:
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return serialize_doc(value)
    if isinstance(value, list):
        return [serialize_value(item) for item in value]
    return value


def safe_regex(text: str | None) -> dict[str, str] | None:
    if not text:
        return None
    return {"$regex": text.strip(), "$options": "i"}


def paging_params(page: int, limit: int) -> tuple[int, int]:
    page = max(page, 1)
    limit = max(min(limit, 100), 1)
    return page, (page - 1) * limit
