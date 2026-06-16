from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config.database import get_database
from app.core.exception_handler import NotFoundException, ValidationException
from app.core.permissions import INVENTORY_READ, INVENTORY_WRITE
from app.core.response_handler import created_response, paginated_response, success_response
from app.core.role_checker import RoleChecker
from app.schemas.stock_schema import StockTransferCreate
from ._route_utils import paging_params, safe_regex, serialize_doc, utc_now, validate_object_id

router = APIRouter()
VALID_STATUS = {"pending", "approved", "completed", "cancelled"}

async def _next_transfer_no(db):
    y = utc_now().year
    seq = await db["counters"].find_one_and_update({"_id": f"st-{y}"}, {"$inc": {"value": 1}}, upsert=True, return_document=True)
    return f"ST-{y}-{seq['value']:04d}"

@router.post("/")
async def create_transfer(data: StockTransferCreate, db: AsyncIOMotorDatabase = Depends(get_database), current_user: dict = Depends(RoleChecker([INVENTORY_WRITE]))):
    payload = data.model_dump(mode="json")
    payload.update({"transfer_no": await _next_transfer_no(db), "status": "pending", "created_by": current_user.get("id") or current_user.get("email"), "created_at": utc_now(), "updated_at": utc_now()})
    res = await db["stock_transfers"].insert_one(payload)
    return created_response(serialize_doc(await db["stock_transfers"].find_one({"_id": res.inserted_id})), "Stock transfer created successfully")

@router.get("/")
async def list_transfers(search: str | None = Query(None), status: str | None = Query(None), page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100), db: AsyncIOMotorDatabase = Depends(get_database), current_user: dict = Depends(RoleChecker([INVENTORY_READ]))):
    page, skip = paging_params(page, limit)
    query = {}
    if status:
        if status not in VALID_STATUS: raise ValidationException("Invalid transfer status")
        query["status"] = status
    rx = safe_regex(search)
    if rx: query["$or"] = [{"transfer_no": rx}, {"items.item_name": rx}]
    total = await db["stock_transfers"].count_documents(query)
    docs = await db["stock_transfers"].find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    return paginated_response([serialize_doc(d) for d in docs], total, page, limit, "Transfers fetched successfully")

@router.get("/{id}")
async def get_transfer(id: str, db: AsyncIOMotorDatabase = Depends(get_database), current_user: dict = Depends(RoleChecker([INVENTORY_READ]))):
    doc = await db["stock_transfers"].find_one({"_id": validate_object_id(id)})
    if not doc: raise NotFoundException("Transfer not found")
    return success_response(serialize_doc(doc), "Transfer fetched successfully")

async def _status(db, id, status, user):
    doc = await db["stock_transfers"].find_one({"_id": validate_object_id(id)})
    if not doc: raise NotFoundException("Transfer not found")
    if status == "completed":
        for item in doc.get("items", []):
            await db["inventory_items"].update_one({"_id": validate_object_id(item["inventory_item_id"], "inventory_item_id")}, {"$inc": {"current_stock": -item["quantity"], "stock_on_hand": -item["quantity"]}, "$set": {"updated_at": utc_now()}})
    await db["stock_transfers"].update_one({"_id": doc["_id"]}, {"$set": {"status": status, "updated_at": utc_now(), f"{status}_by": user.get("id") or user.get("email"), f"{status}_at": utc_now()}})
    return success_response(serialize_doc(await db["stock_transfers"].find_one({"_id": doc["_id"]})), f"Transfer {status} successfully")

@router.patch("/{id}/approve")
async def approve_transfer(id: str, db: AsyncIOMotorDatabase = Depends(get_database), current_user: dict = Depends(RoleChecker([INVENTORY_WRITE]))):
    return await _status(db, id, "approved", current_user)

@router.patch("/{id}/complete")
async def complete_transfer(id: str, db: AsyncIOMotorDatabase = Depends(get_database), current_user: dict = Depends(RoleChecker([INVENTORY_WRITE]))):
    return await _status(db, id, "completed", current_user)
