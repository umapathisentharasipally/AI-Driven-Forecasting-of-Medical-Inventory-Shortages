from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config.database import get_database
from app.core.permissions import INVENTORY_READ
from app.core.response_handler import paginated_response, success_response
from app.core.role_checker import RoleChecker
from ._route_utils import paging_params, serialize_doc

router = APIRouter()

async def _expiring(db, days: int, page: int, limit: int):
    page, skip = paging_params(page, limit)
    today = datetime.now(timezone.utc).date().isoformat()
    end = (datetime.now(timezone.utc).date() + timedelta(days=days)).isoformat()
    query = {"expiry_date": {"$gte": today, "$lte": end}, "available_quantity": {"$gt": 0}}
    total = await db["inventory_batches"].count_documents(query)
    docs = await db["inventory_batches"].find(query).sort("expiry_date", 1).skip(skip).limit(limit).to_list(limit)
    return paginated_response([serialize_doc(d) for d in docs], total, page, limit, f"Items expiring in {days} days fetched successfully")

@router.get("/")
async def list_expiring(days: int = Query(30, ge=1, le=365), page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100), db: AsyncIOMotorDatabase = Depends(get_database), current_user: dict = Depends(RoleChecker([INVENTORY_READ]))):
    return await _expiring(db, days, page, limit)

@router.get("/30-days")
async def expiring_30_days(page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100), db: AsyncIOMotorDatabase = Depends(get_database), current_user: dict = Depends(RoleChecker([INVENTORY_READ]))):
    return await _expiring(db, 30, page, limit)

@router.get("/60-days")
async def expiring_60_days(page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100), db: AsyncIOMotorDatabase = Depends(get_database), current_user: dict = Depends(RoleChecker([INVENTORY_READ]))):
    return await _expiring(db, 60, page, limit)

@router.get("/90-days")
async def expiring_90_days(page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100), db: AsyncIOMotorDatabase = Depends(get_database), current_user: dict = Depends(RoleChecker([INVENTORY_READ]))):
    return await _expiring(db, 90, page, limit)

@router.get("/summary")
async def expiry_summary(db: AsyncIOMotorDatabase = Depends(get_database), current_user: dict = Depends(RoleChecker([INVENTORY_READ]))):
    result = {}
    for days in (30, 60, 90):
        today = datetime.now(timezone.utc).date().isoformat()
        end = (datetime.now(timezone.utc).date() + timedelta(days=days)).isoformat()
        result[f"expiring_{days}_days"] = await db["inventory_batches"].count_documents({"expiry_date": {"$gte": today, "$lte": end}, "available_quantity": {"$gt": 0}})
    return success_response(result, "Expiry summary fetched successfully")
