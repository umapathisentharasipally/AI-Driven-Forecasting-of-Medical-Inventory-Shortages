from typing import List, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.utils.validation_utils import to_object_id


async def get_by_id(db: AsyncIOMotorDatabase, role_id: str) -> Optional[dict]:
    return await db["roles"].find_one({"_id": to_object_id(role_id)})


async def get_by_name(db: AsyncIOMotorDatabase, name: str) -> Optional[dict]:
    return await db["roles"].find_one({"name": name.lower().strip()})

async def get_all(db: AsyncIOMotorDatabase) -> List[dict]:
    cursor = db["roles"].find({}).sort("created_at", 1)
    return await cursor.to_list(length=None)


async def create(db: AsyncIOMotorDatabase, data: dict) -> dict:
    if "name" in data:
        data["name"] = data["name"].lower().strip()

    result = await db["roles"].insert_one(data)
    return await db["roles"].find_one({"_id": result.inserted_id})


async def update(
    db: AsyncIOMotorDatabase,
    role_id: str,
    data: dict,
) -> Optional[dict]:
    if not data:
        return await get_by_id(db, role_id)

    await db["roles"].update_one(
        {"_id": to_object_id(role_id)},
        {"$set": data},
    )
    return await get_by_id(db, role_id)


async def delete(db: AsyncIOMotorDatabase, role_id: str) -> bool:
    result = await db["roles"].delete_one({"_id": to_object_id(role_id)})
    return result.deleted_count == 1