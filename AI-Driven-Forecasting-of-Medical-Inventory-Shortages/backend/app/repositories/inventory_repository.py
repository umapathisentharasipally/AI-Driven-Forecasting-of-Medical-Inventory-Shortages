from datetime import timedelta
from typing import List, Optional, Tuple

from pymongo import ReturnDocument

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.utils.date_utils import utc_now
from app.utils.validation_utils import to_object_id


async def get_by_id(
    db: AsyncIOMotorDatabase,
    id: str,
) -> Optional[dict]:
    return await db["inventory_items"].find_one({"_id": to_object_id(id)})


async def get_by_item_facility(
    db: AsyncIOMotorDatabase,
    item_id: str,
    facility_id: str,
) -> Optional[dict]:
    return await db["inventory_items"].find_one(
        {
            "item_id": item_id,
            "facility_id": facility_id,
        }
    )


def build_inventory_filter(filters: dict) -> dict:
    query: dict = {}

    if filters.get("category"):
        query["category"] = filters["category"]

    if filters.get("facility_id"):
        query["facility_id"] = filters["facility_id"]

    if filters.get("department"):
        query["department_tags"] = filters["department"]

    if filters.get("is_critical") is not None:
        query["is_critical"] = filters["is_critical"]

    if filters.get("is_active") is not None:
        query["is_active"] = filters["is_active"]

    if filters.get("vendor_id"):
        query["vendor_id"] = to_object_id(filters["vendor_id"])

    if filters.get("below_safety_stock") is True:
        query["$expr"] = {
            "$lt": [
                "$current_stock_on_hand",
                "$safety_stock_level",
            ]
        }

    return query


async def get_all(
    db: AsyncIOMotorDatabase,
    page: int,
    limit: int,
    filters: dict,
) -> Tuple[List[dict], int]:
    query = build_inventory_filter(filters)
    skip = (page - 1) * limit

    pipeline = [
        {"$match": query},
        {
            "$facet": {
                "items": [
                    {"$sort": {"updated_at": -1}},
                    {"$skip": skip},
                    {"$limit": limit},
                ],
                "total": [
                    {"$count": "count"},
                ],
            }
        },
    ]

    result = await db["inventory_items"].aggregate(pipeline).to_list(length=1)

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
    result = await db["inventory_items"].insert_one(data)
    created = await db["inventory_items"].find_one({"_id": result.inserted_id})
    return created


async def update(
    db: AsyncIOMotorDatabase,
    id: str,
    data: dict,
) -> Optional[dict]:
    update_data = data.copy()
    update_data["updated_at"] = utc_now()

    if "current_stock_on_hand" in update_data or "avg_daily_usage_last_30d" in update_data:
        existing = await get_by_id(db, id)
        if existing:
            current_stock = update_data.get(
                "current_stock_on_hand",
                existing.get("current_stock_on_hand", 0),
            )
            avg_usage = update_data.get(
                "avg_daily_usage_last_30d",
                existing.get("avg_daily_usage_last_30d", 0),
            )
            update_data["days_of_supply_on_hand"] = (
                current_stock / avg_usage if avg_usage > 0 else 0
            )

    if "current_stock_on_hand" in update_data or "safety_stock_level" in update_data:
        existing = await get_by_id(db, id)
        if existing:
            current_stock = update_data.get(
                "current_stock_on_hand",
                existing.get("current_stock_on_hand", 0),
            )
            safety_stock = update_data.get(
                "safety_stock_level",
                existing.get("safety_stock_level", 0),
            )
            update_data["stock_as_pct_of_safety_level"] = (
                (current_stock / safety_stock) * 100 if safety_stock > 0 else 0
            )

    return await db["inventory_items"].find_one_and_update(
        {"_id": to_object_id(id)},
        {"$set": update_data},
        return_document=ReturnDocument.AFTER,
    )


async def delete(
    db: AsyncIOMotorDatabase,
    id: str,
) -> bool:
    result = await db["inventory_items"].update_one(
        {"_id": to_object_id(id)},
        {
            "$set": {
                "is_active": False,
                "updated_at": utc_now(),
            }
        },
    )
    return result.modified_count == 1


async def adjust_stock_atomic(
    db: AsyncIOMotorDatabase,
    id: str,
    delta: float,
) -> Optional[dict]:
    now = utc_now()

    return await db["inventory_items"].find_one_and_update(
        {
            "_id": to_object_id(id),
            "$expr": {
                "$gte": [
                    {"$add": ["$current_stock_on_hand", float(delta)]},
                    0,
                ]
            },
        },
        [
            {
                "$set": {
                    "current_stock_on_hand": {
                        "$add": ["$current_stock_on_hand", float(delta)]
                    },
                    "snapshot_date": now,
                    "updated_at": now,
                }
            },
            {
                "$set": {
                    "days_of_supply_on_hand": {
                        "$cond": [
                            {"$gt": ["$avg_daily_usage_last_30d", 0]},
                            {
                                "$divide": [
                                    "$current_stock_on_hand",
                                    "$avg_daily_usage_last_30d",
                                ]
                            },
                            0,
                        ]
                    },
                    "stock_as_pct_of_safety_level": {
                        "$cond": [
                            {"$gt": ["$safety_stock_level", 0]},
                            {
                                "$multiply": [
                                    {
                                        "$divide": [
                                            "$current_stock_on_hand",
                                            "$safety_stock_level",
                                        ]
                                    },
                                    100,
                                ]
                            },
                            0,
                        ]
                    },
                }
            },
        ],
        return_document=ReturnDocument.AFTER,
    )


async def get_below_safety_stock(
    db: AsyncIOMotorDatabase,
) -> List[dict]:
    cursor = db["inventory_items"].find(
        {
            "is_active": True,
            "$expr": {
                "$lt": [
                    "$current_stock_on_hand",
                    "$safety_stock_level",
                ]
            },
        }
    ).sort("updated_at", -1)

    return await cursor.to_list(length=None)


async def get_expiring_soon(
    db: AsyncIOMotorDatabase,
    days: int,
) -> List[dict]:
    now = utc_now()
    future = now + timedelta(days=days)

    cursor = db["inventory_items"].find(
        {
            "is_active": True,
            "expiry_date": {
                "$gte": now,
                "$lte": future,
            },
        }
    ).sort("expiry_date", 1)

    return await cursor.to_list(length=None)


async def bulk_upsert(
    db: AsyncIOMotorDatabase,
    items: List[dict],
) -> dict:
    inserted = 0
    updated = 0
    failed = 0

    for item in items:
        try:
            now = utc_now()
            item.setdefault("created_at", now)
            item["updated_at"] = now
            item.setdefault("snapshot_date", now)

            result = await db["inventory_items"].update_one(
                {
                    "item_id": item["item_id"],
                    "facility_id": item["facility_id"],
                },
                {
                    "$set": item,
                    "$setOnInsert": {
                        "created_at": item["created_at"],
                    },
                },
                upsert=True,
            )

            if result.upserted_id:
                inserted += 1
            else:
                updated += result.modified_count

        except Exception:
            failed += 1

    return {
        "inserted": inserted,
        "updated": updated,
        "failed": failed,
    }