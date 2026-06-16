from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config.database import get_database
from app.core.exception_handler import NotFoundException
from app.core.permissions import INVENTORY_READ, INVENTORY_WRITE
from app.core.response_handler import created_response, paginated_response, success_response
from app.core.role_checker import RoleChecker
from app.schemas.stock_schema import StockReceiptCreate
from ._route_utils import paging_params, safe_regex, serialize_doc, utc_now, validate_object_id

router = APIRouter()

async def _next_number(db, prefix):
    y = utc_now().year
    seq = await db["counters"].find_one_and_update({"_id": f"{prefix}-{y}"}, {"$inc": {"value": 1}}, upsert=True, return_document=True)
    return f"{prefix.upper()}-{y}-{seq['value']:04d}"

@router.post("/")
async def create_receipt(data: StockReceiptCreate, db: AsyncIOMotorDatabase = Depends(get_database), current_user: dict = Depends(RoleChecker([INVENTORY_WRITE]))):
    payload = data.model_dump(mode="json")
    payload.update({"receipt_no": await _next_number(db, "rc"), "received_by": current_user.get("id") or current_user.get("email"), "created_at": utc_now(), "updated_at": utc_now()})
    res = await db["stock_receipts"].insert_one(payload)
    for item in payload["items"]:
        await db["inventory_items"].update_one({"_id": validate_object_id(item["inventory_item_id"], "inventory_item_id")}, {"$inc": {"current_stock": item["quantity"], "stock_on_hand": item["quantity"]}, "$set": {"updated_at": utc_now()}})
        if item.get("batch_no") or item.get("expiry_date"):
            await db["inventory_batches"].insert_one({**item, "receipt_id": str(res.inserted_id), "available_quantity": item["quantity"], "created_at": utc_now()})
    if payload.get("purchase_order_id"):
        await db["purchase_orders"].update_one({"_id": validate_object_id(payload["purchase_order_id"], "purchase_order_id")}, {"$set": {"status": "received", "updated_at": utc_now()}})
    return created_response(serialize_doc(await db["stock_receipts"].find_one({"_id": res.inserted_id})), "Stock receipt created successfully")

@router.get("/")
async def list_receipts(search: str | None = Query(None), page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100), db: AsyncIOMotorDatabase = Depends(get_database), current_user: dict = Depends(RoleChecker([INVENTORY_READ]))):
    page, skip = paging_params(page, limit)
    query = {}
    rx = safe_regex(search)
    if rx: query["$or"] = [{"receipt_no": rx}, {"vendor_name": rx}, {"items.item_name": rx}]
    total = await db["stock_receipts"].count_documents(query)
    docs = await db["stock_receipts"].find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    return paginated_response([serialize_doc(d) for d in docs], total, page, limit, "Receipts fetched successfully")

@router.get("/recent")
async def recent_receipts(limit: int = Query(5, ge=1, le=20), db: AsyncIOMotorDatabase = Depends(get_database), current_user: dict = Depends(RoleChecker([INVENTORY_READ]))):
    docs = await db["stock_receipts"].find({}).sort("created_at", -1).limit(limit).to_list(limit)
    return success_response([serialize_doc(d) for d in docs], "Recent receipts fetched successfully")

@router.get("/{id}")
async def get_receipt(id: str, db: AsyncIOMotorDatabase = Depends(get_database), current_user: dict = Depends(RoleChecker([INVENTORY_READ]))):
    doc = await db["stock_receipts"].find_one({"_id": validate_object_id(id)})
    if not doc: raise NotFoundException("Receipt not found")
    return success_response(serialize_doc(doc), "Receipt fetched successfully")
