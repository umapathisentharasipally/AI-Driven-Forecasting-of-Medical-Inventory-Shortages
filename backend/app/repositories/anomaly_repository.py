from typing import List, Optional, Tuple

from pymongo import ReturnDocument
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.utils.date_utils import parse_date, utc_now
from app.utils.validation_utils import to_object_id


async def create(
    db: AsyncIOMotorDatabase,
    data: dict,
) -> dict:
    result = await db["anomalies"].insert_one(data)
    return await db["anomalies"].find_one({"_id": result.inserted_id})


async def get_by_id(
    db: AsyncIOMotorDatabase,
    id: str,
) -> Optional[dict]:
    return await db["anomalies"].find_one({"_id": to_object_id(id)})


def _build_anomaly_filter(filters: dict) -> dict:
    query: dict = {}

    if filters.get("item_id"):
        query["item_id"] = filters["item_id"]

    if filters.get("facility_id"):
        query["facility_id"] = filters["facility_id"]

    if filters.get("is_anomaly") is not None:
        query["is_anomaly"] = filters["is_anomaly"]

    if filters.get("is_acknowledged") is not None:
        query["is_acknowledged"] = filters["is_acknowledged"]

    date_filter = {}
    if filters.get("date_from"):
        date_filter["$gte"] = parse_date(filters["date_from"])

    if filters.get("date_to"):
        date_filter["$lte"] = parse_date(filters["date_to"])

    if date_filter:
        query["detected_at"] = date_filter

    return query


async def get_all(
    db: AsyncIOMotorDatabase,
    page: int,
    limit: int,
    filters: dict,
) -> Tuple[List[dict], int]:
    query = _build_anomaly_filter(filters)
    skip = (page - 1) * limit

    pipeline = [
        {"$match": query},
        {
            "$facet": {
                "items": [
                    {"$sort": {"detected_at": -1}},
                    {"$skip": skip},
                    {"$limit": limit},
                ],
                "total": [
                    {"$count": "count"},
                ],
            }
        },
    ]

    result = await db["anomalies"].aggregate(pipeline).to_list(length=1)

    if not result:
        return [], 0

    items = result[0].get("items", [])
    total_data = result[0].get("total", [])
    total = total_data[0]["count"] if total_data else 0

    return items, total


async def get_unacknowledged(
    db: AsyncIOMotorDatabase,
    page: int,
    limit: int,
) -> Tuple[List[dict], int]:
    return await get_all(
        db=db,
        page=page,
        limit=limit,
        filters={
            "is_acknowledged": False,
        },
    )


async def acknowledge(
    db: AsyncIOMotorDatabase,
    id: str,
    user_id: str,
    notes: str | None,
) -> Optional[dict]:
    return await db["anomalies"].find_one_and_update(
        {"_id": to_object_id(id)},
        {
            "$set": {
                "is_acknowledged": True,
                "acknowledged_by": user_id,
                "acknowledged_at": utc_now(),
                "notes": notes,
            }
        },
        return_document=ReturnDocument.AFTER,
    )


async def bulk_create(
    db: AsyncIOMotorDatabase,
    anomalies: List[dict],
) -> int:
    if not anomalies:
        return 0

    result = await db["anomalies"].insert_many(anomalies)
    return len(result.inserted_ids)