from datetime import timedelta
from typing import List, Optional, Tuple

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

from app.utils.date_utils import parse_date, utc_now
from app.utils.validation_utils import to_object_id


async def create(db: AsyncIOMotorDatabase, data: dict) -> dict:
    result = await db["alerts"].insert_one(data)
    return await db["alerts"].find_one({"_id": result.inserted_id})


async def get_by_id(db: AsyncIOMotorDatabase, id: str) -> Optional[dict]:
    return await db["alerts"].find_one({"_id": to_object_id(id)})


def _build_filter(filters: dict) -> dict:
    query: dict = {}

    for field in [
        "status",
        "severity",
        "alert_type",
        "item_id",
        "facility_id",
        "assigned_to",
    ]:
        if filters.get(field) is not None:
            query[field] = filters[field]

    date_filter = {}
    if filters.get("date_from"):
        date_filter["$gte"] = parse_date(filters["date_from"])
    if filters.get("date_to"):
        date_filter["$lte"] = parse_date(filters["date_to"])

    if date_filter:
        query["created_at"] = date_filter

    return query


async def get_all(
    db: AsyncIOMotorDatabase,
    page: int,
    limit: int,
    filters: dict,
) -> Tuple[List[dict], int]:
    query = _build_filter(filters)
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
                "total": [{"$count": "count"}],
            }
        },
    ]

    result = await db["alerts"].aggregate(pipeline).to_list(length=1)

    if not result:
        return [], 0

    items = result[0].get("items", [])
    total_data = result[0].get("total", [])
    total = total_data[0]["count"] if total_data else 0

    return items, total


async def find_existing_open(
    db: AsyncIOMotorDatabase,
    item_id: str,
    facility_id: str,
    alert_type: str,
) -> Optional[dict]:
    return await db["alerts"].find_one(
        {
            "item_id": item_id,
            "facility_id": facility_id,
            "alert_type": alert_type,
            "status": "open",
        }
    )


async def update_status(
    db: AsyncIOMotorDatabase,
    id: str,
    status: str,
    extra_fields: dict | None = None,
) -> Optional[dict]:
    update_data = {
        "status": status,
        "updated_at": utc_now(),
    }

    if extra_fields:
        update_data.update(extra_fields)

    return await db["alerts"].find_one_and_update(
        {"_id": to_object_id(id)},
        {"$set": update_data},
        return_document=ReturnDocument.AFTER,
    )


async def assign(
    db: AsyncIOMotorDatabase,
    id: str,
    user_id: str,
) -> Optional[dict]:
    return await db["alerts"].find_one_and_update(
        {"_id": to_object_id(id)},
        {
            "$set": {
                "assigned_to": user_id,
                "updated_at": utc_now(),
            }
        },
        return_document=ReturnDocument.AFTER,
    )


async def get_dashboard_counts(db: AsyncIOMotorDatabase) -> dict:
    now = utc_now()
    start_today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    pipeline = [
        {
            "$facet": {
                "critical": [
                    {"$match": {"severity": "Critical", "status": "open"}},
                    {"$count": "count"},
                ],
                "high": [
                    {"$match": {"severity": "High", "status": "open"}},
                    {"$count": "count"},
                ],
                "medium": [
                    {"$match": {"severity": "Medium", "status": "open"}},
                    {"$count": "count"},
                ],
                "low": [
                    {"$match": {"severity": "Low", "status": "open"}},
                    {"$count": "count"},
                ],
                "open_total": [
                    {"$match": {"status": "open"}},
                    {"$count": "count"},
                ],
                "resolved_today": [
                    {
                        "$match": {
                            "status": "resolved",
                            "resolved_at": {"$gte": start_today},
                        }
                    },
                    {"$count": "count"},
                ],
                "snoozed": [
                    {"$match": {"status": "snoozed"}},
                    {"$count": "count"},
                ],
            }
        }
    ]

    result = await db["alerts"].aggregate(pipeline).to_list(length=1)
    data = result[0] if result else {}

    def count(name: str) -> int:
        values = data.get(name, [])
        return values[0]["count"] if values else 0

    return {
        "critical": count("critical"),
        "high": count("high"),
        "medium": count("medium"),
        "low": count("low"),
        "open_total": count("open_total"),
        "resolved_today": count("resolved_today"),
        "snoozed": count("snoozed"),
    }