from typing import List, Tuple

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.utils.validation_utils import to_object_id


async def bulk_create(
    db: AsyncIOMotorDatabase,
    notifications: List[dict],
) -> int:
    if not notifications:
        return 0

    result = await db["notifications"].insert_many(notifications)
    return len(result.inserted_ids)


async def get_for_user(
    db: AsyncIOMotorDatabase,
    user_id: str,
    page: int,
    limit: int,
    unread_first: bool = True,
) -> Tuple[List[dict], int]:
    skip = (page - 1) * limit

    sort_stage = {"is_read": 1, "created_at": -1} if unread_first else {"created_at": -1}

    pipeline = [
        {"$match": {"user_id": user_id}},
        {
            "$facet": {
                "items": [
                    {"$sort": sort_stage},
                    {"$skip": skip},
                    {"$limit": limit},
                ],
                "total": [{"$count": "count"}],
            }
        },
    ]

    result = await db["notifications"].aggregate(pipeline).to_list(length=1)

    if not result:
        return [], 0

    items = result[0].get("items", [])
    total_data = result[0].get("total", [])
    total = total_data[0]["count"] if total_data else 0

    return items, total


async def mark_read(
    db: AsyncIOMotorDatabase,
    user_id: str,
    notification_ids: List[str],
) -> int:
    object_ids = [to_object_id(id) for id in notification_ids]

    result = await db["notifications"].update_many(
        {
            "_id": {"$in": object_ids},
            "user_id": user_id,
        },
        {"$set": {"is_read": True}},
    )

    return result.modified_count


async def mark_all_read(
    db: AsyncIOMotorDatabase,
    user_id: str,
) -> int:
    result = await db["notifications"].update_many(
        {
            "user_id": user_id,
            "is_read": False,
        },
        {"$set": {"is_read": True}},
    )

    return result.modified_count


async def get_unread_count(
    db: AsyncIOMotorDatabase,
    user_id: str,
) -> int:
    return await db["notifications"].count_documents(
        {
            "user_id": user_id,
            "is_read": False,
        }
    )