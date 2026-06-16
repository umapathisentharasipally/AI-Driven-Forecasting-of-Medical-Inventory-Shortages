from datetime import datetime, timezone, date
from decimal import Decimal
from typing import Any, Tuple

from bson import ObjectId
from fastapi import HTTPException, Query, status


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def validate_object_id(value: str) -> ObjectId:
    if not ObjectId.is_valid(value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ObjectId",
        )
    return ObjectId(value)


def safe_regex(search: str | None) -> dict | None:
    if not search:
        return None

    escaped = (
        search.replace("\\", "\\\\")
        .replace(".", "\\.")
        .replace("*", "\\*")
        .replace("+", "\\+")
        .replace("?", "\\?")
        .replace("|", "\\|")
        .replace("{", "\\{")
        .replace("}", "\\}")
        .replace("(", "\\(")
        .replace(")", "\\)")
        .replace("[", "\\[")
        .replace("]", "\\]")
        .replace("^", "\\^")
        .replace("$", "\\$")
    )

    return {"$regex": escaped, "$options": "i"}


def paging_params(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> Tuple[int, int]:
    return limit, offset


def serialize_doc(data: Any) -> Any:
    if isinstance(data, ObjectId):
        return str(data)

    if isinstance(data, (datetime, date)):
        return data.isoformat()

    if isinstance(data, Decimal):
        return float(data)

    if isinstance(data, list):
        return [serialize_doc(item) for item in data]

    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if key == "_id":
                result["id"] = str(value)
            else:
                result[key] = serialize_doc(value)
        return result

    return data