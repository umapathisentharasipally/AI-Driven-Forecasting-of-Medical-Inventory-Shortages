from typing import List, Optional, Tuple

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.utils.validation_utils import to_object_id


async def create(db: AsyncIOMotorDatabase, data: dict) -> dict:
    result = await db["reports"].insert_one(data)
    return await db["reports"].find_one({"_id": result.inserted_id})


async def get_by_id(db: AsyncIOMotorDatabase, id: str) -> Optional[dict]:
    return await db["reports"].find_one({"_id": to_object_id(id)})


async def get_all(
    db: AsyncIOMotorDatabase,
    page: int,
    limit: int,
    report_type: str | None,
) -> Tuple[List[dict], int]:
    query = {}
    if report_type:
        query["report_type"] = report_type

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

    result = await db["reports"].aggregate(pipeline).to_list(length=1)
    if not result:
        return [], 0

    items = result[0].get("items", [])
    total_data = result[0].get("total", [])
    total = total_data[0]["count"] if total_data else 0

    return items, total


async def update_status(
    db: AsyncIOMotorDatabase,
    id: str,
    status: str,
    file_path: str | None,
    summary: dict | None,
) -> None:
    await db["reports"].update_one(
        {"_id": to_object_id(id)},
        {
            "$set": {
                "status": status,
                "file_path": file_path,
                "summary": summary,
            }
        },
    )