from typing import List, Tuple

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.repositories import notification_repository
from app.schemas.notification_schema import NotificationResponse
from app.utils.validation_utils import validate_pagination


def to_notification_response(notification: dict) -> NotificationResponse:
    return NotificationResponse(
        id=str(notification["_id"]),
        user_id=notification["user_id"],
        alert_id=notification.get("alert_id"),
        channel=notification["channel"],
        title=notification["title"],
        body=notification["body"],
        is_read=bool(notification["is_read"]),
        sent_at=notification.get("sent_at"),
        created_at=notification["created_at"],
    )


async def get_notifications(
    db: AsyncIOMotorDatabase,
    user_id: str,
    page: int,
    limit: int,
) -> Tuple[List[NotificationResponse], int]:
    page, limit = validate_pagination(page, limit)

    notifications, total = await notification_repository.get_for_user(
        db=db,
        user_id=user_id,
        page=page,
        limit=limit,
        unread_first=True,
    )

    return [to_notification_response(item) for item in notifications], total


async def mark_read(
    db: AsyncIOMotorDatabase,
    user_id: str,
    ids: List[str],
) -> int:
    return await notification_repository.mark_read(db, user_id, ids)


async def mark_all_read(
    db: AsyncIOMotorDatabase,
    user_id: str,
) -> int:
    return await notification_repository.mark_all_read(db, user_id)


async def get_unread_count(
    db: AsyncIOMotorDatabase,
    user_id: str,
) -> int:
    return await notification_repository.get_unread_count(db, user_id)