from datetime import date
from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config.database import get_database
from app.core.exception_handler import NotFoundException, ValidationException
from app.core.permissions import INVENTORY_READ, INVENTORY_WRITE
from app.core.response_handler import created_response, paginated_response, success_response
from app.core.role_checker import RoleChecker
from app.schemas.procurement_schema import PurchaseOrderCreate, PurchaseOrderUpdate
from ._route_utils import paging_params, safe_regex, serialize_doc, utc_now, validate_object_id

router = APIRouter()
VALID_STATUS = {"draft", "pending", "approved", "rejected", "shipped", "partially_received", "received", "cancelled"}

async def _next_po_number(db: AsyncIOMotorDatabase) -> str:
    year = utc_now().year
    seq = await db["counters"].find_one_and_update({"_id": f"po-{year}"}, {"$inc": {"value": 1}}, upsert=True, return_document=True)
    return f"PO-{year}-{seq['value']:04d}"

def _total(items):
    return round(sum(float(i.get("quantity", 0)) * float(i.get("unit_price", 0)) for i in items), 2)

@router.post("/")
async def create_purchase_order(data: PurchaseOrderCreate, db: AsyncIOMotorDatabase = Depends(get_database), current_user: dict = Depends(RoleChecker([INVENTORY_WRITE]))):
    payload = data.model_dump(mode="json")
    payload.update({"po_number": await _next_po_number(db), "status": "pending", "total_amount": _total(payload["items"]), "created_by": current_user.get("id") or current_user.get("email"), "created_at": utc_now(), "updated_at": utc_now()})
    res = await db["purchase_orders"].insert_one(payload)
    return created_response(serialize_doc(await db["purchase_orders"].find_one({"_id": res.inserted_id})), "Purchase order created successfully")

@router.get("/")
async def list_purchase_orders(search: str | None = Query(None), status: str | None = Query(None), vendor_id: str | None = Query(None), page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100), db: AsyncIOMotorDatabase = Depends(get_database), current_user: dict = Depends(RoleChecker([INVENTORY_READ]))):
    page, skip = paging_params(page, limit)
    query = {}
    if status:
        if status not in VALID_STATUS: raise ValidationException("Invalid purchase order status")
        query["status"] = status
    if vendor_id: query["vendor_id"] = vendor_id
    rx = safe_regex(search)
    if rx: query["$or"] = [{"po_number": rx}, {"vendor_name": rx}, {"items.item_name": rx}]
    total = await db["purchase_orders"].count_documents(query)
    docs = await db["purchase_orders"].find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    return paginated_response([serialize_doc(d) for d in docs], total, page, limit, "Purchase orders fetched successfully")

@router.get("/{id}")
async def get_purchase_order(id: str, db: AsyncIOMotorDatabase = Depends(get_database), current_user: dict = Depends(RoleChecker([INVENTORY_READ]))):
    doc = await db["purchase_orders"].find_one({"_id": validate_object_id(id)})
    if not doc: raise NotFoundException("Purchase order not found")
    return success_response(serialize_doc(doc), "Purchase order fetched successfully")

@router.patch("/{id}")
async def update_purchase_order(id: str, data: PurchaseOrderUpdate, db: AsyncIOMotorDatabase = Depends(get_database), current_user: dict = Depends(RoleChecker([INVENTORY_WRITE]))):
    payload = {k:v for k,v in data.model_dump(mode="json", exclude_unset=True).items() if v is not None}
    payload["updated_at"] = utc_now()
    res = await db["purchase_orders"].update_one({"_id": validate_object_id(id), "status": {"$in": ["draft", "pending"]}}, {"$set": payload})
    if res.matched_count == 0: raise NotFoundException("Editable purchase order not found")
    return success_response(serialize_doc(await db["purchase_orders"].find_one({"_id": validate_object_id(id)})), "Purchase order updated successfully")

async def _set_status(db, id: str, status: str, user: dict, extra: dict | None = None):
    payload = {"status": status, "updated_at": utc_now(), f"{status}_by": user.get("id") or user.get("email"), f"{status}_at": utc_now()}
    if extra: payload.update(extra)
    res = await db["purchase_orders"].update_one({"_id": validate_object_id(id)}, {"$set": payload})
    if res.matched_count == 0: raise NotFoundException("Purchase order not found")
    return success_response(serialize_doc(await db["purchase_orders"].find_one({"_id": validate_object_id(id)})), f"Purchase order {status} successfully")

@router.patch("/{id}/approve")
async def approve_purchase_order(id: str, db: AsyncIOMotorDatabase = Depends(get_database), current_user: dict = Depends(RoleChecker([INVENTORY_WRITE]))):
    return await _set_status(db, id, "approved", current_user)

@router.patch("/{id}/reject")
async def reject_purchase_order(id: str, reason: str | None = None, db: AsyncIOMotorDatabase = Depends(get_database), current_user: dict = Depends(RoleChecker([INVENTORY_WRITE]))):
    return await _set_status(db, id, "rejected", current_user, {"reject_reason": reason})

@router.patch("/{id}/ship")
async def ship_purchase_order(id: str, db: AsyncIOMotorDatabase = Depends(get_database), current_user: dict = Depends(RoleChecker([INVENTORY_WRITE]))):
    return await _set_status(db, id, "shipped", current_user)

@router.patch("/{id}/receive")
async def receive_purchase_order(id: str, db: AsyncIOMotorDatabase = Depends(get_database), current_user: dict = Depends(RoleChecker([INVENTORY_WRITE]))):
    return await _set_status(db, id, "received", current_user, {"received_date": date.today().isoformat()})

@router.delete("/{id}")
async def cancel_purchase_order(id: str, db: AsyncIOMotorDatabase = Depends(get_database), current_user: dict = Depends(RoleChecker([INVENTORY_WRITE]))):
    return await _set_status(db, id, "cancelled", current_user)
