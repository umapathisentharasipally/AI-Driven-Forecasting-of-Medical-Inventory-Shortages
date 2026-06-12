from typing import List, Optional, Tuple

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.utils.date_utils import utc_now
from app.utils.validation_utils import to_object_id


async def get_by_id(db: AsyncIOMotorDatabase, user_id: str) -> Optional[dict]:
    return await db["users"].find_one({"_id": to_object_id(user_id)})


async def get_by_email(db: AsyncIOMotorDatabase, email: str) -> Optional[dict]:
    return await db["users"].find_one({"email": email})


async def get_all(
    db: AsyncIOMotorDatabase,
    page: int,
    limit: int,
    filters: dict,
) -> Tuple[List[dict], int]:
    match_filter = {}

    if filters.get("department"):
        match_filter["department"] = filters["department"]

    if filters.get("role_id"):
        match_filter["role_id"] = to_object_id(filters["role_id"])

    if filters.get("is_active") is not None:
        match_filter["is_active"] = filters["is_active"]

    skip = (page - 1) * limit

    pipeline = [
        {"$match": match_filter},
        {
            "$facet": {
                "items": [
                    {"$sort": {"created_at": -1}},
                    {"$skip": skip},
                    {"$limit": limit},
                ],
                "total": [
                    {"$count": "count"},
                ],
            }
        },
    ]

    result = await db["users"].aggregate(pipeline).to_list(length=1)

    if not result:
        return [], 0

    items = result[0].get("items", [])
    total_data = result[0].get("total", [])
    total = total_data[0]["count"] if total_data else 0

    return items, total


async def create(db: AsyncIOMotorDatabase, data: dict) -> dict:
    result = await db["users"].insert_one(data)
    return await db["users"].find_one({"_id": result.inserted_id})


async def update(
    db: AsyncIOMotorDatabase,
    user_id: str,
    data: dict,
) -> Optional[dict]:
    update_data = data.copy()
    update_data["updated_at"] = utc_now()

    await db["users"].update_one(
        {"_id": to_object_id(user_id)},
        {"$set": update_data},
    )
    return await get_by_id(db, user_id)


async def soft_delete(db: AsyncIOMotorDatabase, user_id: str) -> bool:
    result = await db["users"].update_one(
        {"_id": to_object_id(user_id)},
        {
            "$set": {
                "is_active": False,
                "updated_at": utc_now(),
            }
        },
    )
    return result.modified_count == 1


async def update_last_login(db: AsyncIOMotorDatabase, user_id: str) -> None:
    await db["users"].update_one(
        {"_id": to_object_id(user_id)},
        {
            "$set": {
                "last_login": utc_now(),
                "updated_at": utc_now(),
            }
        },
    )