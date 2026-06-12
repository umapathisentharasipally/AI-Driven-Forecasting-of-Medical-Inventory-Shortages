from typing import List, Optional, Tuple

from pymongo import ReturnDocument

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.utils.date_utils import utc_now
from app.utils.validation_utils import to_object_id


async def get_by_id(
    db: AsyncIOMotorDatabase,
    vendor_id: str,
) -> Optional[dict]:
    return await db["vendors"].find_one({"_id": to_object_id(vendor_id)})


async def get_by_vendor_code(
    db: AsyncIOMotorDatabase,
    vendor_code: str,
) -> Optional[dict]:
    return await db["vendors"].find_one({"vendor_code": vendor_code})


async def get_all(
    db: AsyncIOMotorDatabase,
    page: int,
    limit: int,
    is_active: Optional[bool] = None,
) -> Tuple[List[dict], int]:
    query = {}

    if is_active is not None:
        query["is_active"] = is_active

    skip = (page - 1) * limit

    pipeline = [
        {"$match": query},
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

    result = await db["vendors"].aggregate(pipeline).to_list(length=1)

    if not result:
        return [], 0

    items = result[0].get("items", [])
    total_data = result[0].get("total", [])
    total = total_data[0]["count"] if total_data else 0

    return items, total


async def create(
    db: AsyncIOMotorDatabase,
    data: dict,
) -> dict:
    result = await db["vendors"].insert_one(data)
    return await db["vendors"].find_one({"_id": result.inserted_id})


async def update(
    db: AsyncIOMotorDatabase,
    vendor_id: str,
    data: dict,
) -> Optional[dict]:
    if not data:
        return await get_by_id(db, vendor_id)

    return await db["vendors"].find_one_and_update(
        {"_id": to_object_id(vendor_id)},
        {"$set": data},
        return_document=ReturnDocument.AFTER,
    )


async def soft_delete(
    db: AsyncIOMotorDatabase,
    vendor_id: str,
) -> bool:
    result = await db["vendors"].update_one(
        {"_id": to_object_id(vendor_id)},
        {"$set": {"is_active": False}},
    )
    return result.modified_count == 1


async def update_reliability_score(
    db: AsyncIOMotorDatabase,
    vendor_id: str,
    reliability_score: float,
) -> Optional[dict]:
    return await db["vendors"].find_one_and_update(
        {"_id": to_object_id(vendor_id)},
        {"$set": {"reliability_score": reliability_score}},
        return_document=ReturnDocument.AFTER,
    )