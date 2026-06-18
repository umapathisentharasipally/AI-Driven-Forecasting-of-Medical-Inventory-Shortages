from typing import List, Tuple

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.utils.date_utils import parse_date
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def create(db: AsyncIOMotorDatabase, log: dict) -> None:
    try:
        await db["audit_logs"].insert_one(log)
    except Exception as exc:
        logger.error(f"Audit log insert failed: {exc}")


def _build_filter(filters: dict) -> dict:
    query: dict = {}

    if filters.get("user_id"):
        query["user_id"] = filters["user_id"]

    if filters.get("action"):
        query["action"] = filters["action"]

    if filters.get("resource_type"):
        query["resource_type"] = filters["resource_type"]

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

    result = await db["audit_logs"].aggregate(pipeline).to_list(length=1)

    if not result:
        return [], 0

    items = result[0].get("items", [])
    total_data = result[0].get("total", [])
    total = total_data[0]["count"] if total_data else 0

    return items, total


async def get_by_user(
    db: AsyncIOMotorDatabase,
    user_id: str,
    page: int,
    limit: int,
) -> Tuple[List[dict], int]:
    return await get_all(
        db=db,
        page=page,
        limit=limit,
        filters={"user_id": user_id},
    )


async def get_by_resource(
    db: AsyncIOMotorDatabase,
    resource_type: str,
    resource_id: str,
    page: int,
    limit: int,
) -> Tuple[List[dict], int]:
    skip = (page - 1) * limit

    pipeline = [
        {
            "$match": {
                "resource_type": resource_type,
                "resource_id": resource_id,
            }
        },
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

    result = await db["audit_logs"].aggregate(pipeline).to_list(length=1)

    if not result:
        return [], 0

    items = result[0].get("items", [])
    total_data = result[0].get("total", [])
    total = total_data[0]["count"] if total_data else 0

    return items, total