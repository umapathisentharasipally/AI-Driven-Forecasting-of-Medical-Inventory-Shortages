from typing import List, Optional, Tuple

from pymongo import ReturnDocument
from motor.motor_asyncio import AsyncIOMotorDatabase


async def upsert(
    db: AsyncIOMotorDatabase,
    item_id: str | None,
    facility_id: str | None,
    period: str,
    data: dict,
) -> dict:
    return await db["trends"].find_one_and_update(
        {
            "item_id": item_id,
            "facility_id": facility_id,
            "period": period,
        },
        {"$set": data},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )


async def get_for_item(
    db: AsyncIOMotorDatabase,
    item_id: str,
    facility_id: str,
    period: str,
) -> List[dict]:
    cursor = db["trends"].find(
        {
            "item_id": item_id,
            "facility_id": facility_id,
            "period": period,
        }
    ).sort("computed_at", -1)

    return await cursor.to_list(length=None)


async def get_all(
    db: AsyncIOMotorDatabase,
    page: int,
    limit: int,
) -> Tuple[List[dict], int]:
    skip = (page - 1) * limit

    pipeline = [
        {
            "$facet": {
                "items": [
                    {"$sort": {"computed_at": -1}},
                    {"$skip": skip},
                    {"$limit": limit},
                ],
                "total": [
                    {"$count": "count"},
                ],
            }
        },
    ]

    result = await db["trends"].aggregate(pipeline).to_list(length=1)

    if not result:
        return [], 0

    items = result[0].get("items", [])
    total_data = result[0].get("total", [])
    total = total_data[0]["count"] if total_data else 0

    return items, total