from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config.settings import settings
from app.core.exception_handler import DatabaseException

_client: Optional[AsyncIOMotorClient] = None
_database: Optional[AsyncIOMotorDatabase] = None


async def connect_db() -> None:
    global _client, _database
    if _client is None:
        _client = AsyncIOMotorClient(settings.MONGO_URI)
        _database = _client[settings.DB_NAME]


def get_db_client() -> AsyncIOMotorClient:
    if _client is None:
        raise DatabaseException("Database client is not initialized")
    return _client


async def get_database() -> AsyncIOMotorDatabase:
    if _database is None:
        await connect_db()
    if _database is None:
        raise DatabaseException("Database is not initialized")
    return _database


async def close_db_connection() -> None:
    global _client, _database
    if _client is not None:
        _client.close()
    _client = None
    _database = None


async def get_users_collection():
    return (await get_database())["users"]


async def get_roles_collection():
    return (await get_database())["roles"]


async def get_inventory_collection():
    return (await get_database())["inventory_items"]


async def get_vendors_collection():
    return (await get_database())["vendors"]


async def get_predictions_collection():
    return (await get_database())["predictions"]


async def get_anomalies_collection():
    return (await get_database())["anomalies"]


async def get_trends_collection():
    return (await get_database())["trends"]


async def get_alerts_collection():
    return (await get_database())["alerts"]


async def get_reports_collection():
    return (await get_database())["reports"]


async def get_notifications_collection():
    return (await get_database())["notifications"]


async def get_audit_logs_collection():
    return (await get_database())["audit_logs"]


async def get_consumption_logs_collection():
    return (await get_database())["consumption_logs"]