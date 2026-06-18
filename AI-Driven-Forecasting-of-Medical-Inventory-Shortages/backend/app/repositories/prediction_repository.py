from datetime import time
from typing import List, Optional, Tuple

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.utils.date_utils import parse_date, utc_now
from app.utils.validation_utils import to_object_id


async def create(
    db: AsyncIOMotorDatabase,
    data: dict,
) -> dict:
    result = await db["predictions"].insert_one(data)
    return await db["predictions"].find_one({"_id": result.inserted_id})


async def get_by_id(
    db: AsyncIOMotorDatabase,
    id: str,
) -> Optional[dict]:
    return await db["predictions"].find_one({"_id": to_object_id(id)})


async def get_latest_for_item(
    db: AsyncIOMotorDatabase,
    item_id: str,
    facility_id: str,
) -> Optional[dict]:
    return await db["predictions"].find_one(
        {
            "item_id": item_id,
            "facility_id": facility_id,
        },
        sort=[("prediction_date", -1)],
    )


def _build_prediction_filter(filters: dict) -> dict:
    query: dict = {}

    if filters.get("item_id"):
        query["item_id"] = filters["item_id"]

    if filters.get("facility_id"):
        query["facility_id"] = filters["facility_id"]

    if filters.get("risk_level"):
        query["risk_level"] = filters["risk_level"]

    date_filter = {}
    if filters.get("date_from"):
        date_filter["$gte"] = parse_date(filters["date_from"])

    if filters.get("date_to"):
        date_filter["$lte"] = parse_date(filters["date_to"])

    if date_filter:
        query["prediction_date"] = date_filter

    return query


async def get_all(
    db: AsyncIOMotorDatabase,
    page: int,
    limit: int,
    filters: dict,
) -> Tuple[List[dict], int]:
    query = _build_prediction_filter(filters)
    skip = (page - 1) * limit

    pipeline = [
        {"$match": query},
        {
            "$facet": {
                "items": [
                    {"$sort": {"prediction_date": -1}},
                    {"$skip": skip},
                    {"$limit": limit},
                ],
                "total": [
                    {"$count": "count"},
                ],
            }
        },
    ]

    result = await db["predictions"].aggregate(pipeline).to_list(length=1)

    if not result:
        return [], 0

    items = result[0].get("items", [])
    total_data = result[0].get("total", [])
    total = total_data[0]["count"] if total_data else 0

    return items, total


async def get_high_risk(
    db: AsyncIOMotorDatabase,
    threshold: float = 0.7,
) -> List[dict]:
    cursor = db["predictions"].find(
        {
            "stockout_probability": {"$gte": threshold},
        }
    ).sort("stockout_probability", -1)

    return await cursor.to_list(length=None)


async def bulk_create(
    db: AsyncIOMotorDatabase,
    predictions: List[dict],
) -> int:
    if not predictions:
        return 0

    result = await db["predictions"].insert_many(predictions)
    return len(result.inserted_ids)


async def already_predicted_today(
    db: AsyncIOMotorDatabase,
    inventory_doc_id: str,
) -> bool:
    now = utc_now()
    start_of_today = now.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    existing = await db["predictions"].find_one(
        {
            "inventory_doc_id": inventory_doc_id,
            "prediction_date": {"$gte": start_of_today},
        }
    )

    return existing is not None