import html

from bson import ObjectId

from app.config.settings import settings
from app.core.exception_handler import ValidationException


def is_valid_object_id(id: str) -> bool:
    return ObjectId.is_valid(id)


def to_object_id(id: str) -> ObjectId:
    if not ObjectId.is_valid(id):
        raise ValidationException("Invalid ObjectId", details={"id": id})
    return ObjectId(id)


def validate_pagination(page: int, limit: int) -> tuple[int, int]:
    if page < 1:
        raise ValidationException("Page must be greater than or equal to 1")

    if limit < 1:
        raise ValidationException("Limit must be greater than or equal to 1")

    if limit > settings.PAGE_SIZE_MAX:
        raise ValidationException(
            f"Limit cannot exceed {settings.PAGE_SIZE_MAX}",
            details={"max_limit": settings.PAGE_SIZE_MAX},
        )

    return page, limit


def sanitize_string(s: str) -> str:
    return html.escape(s.strip())