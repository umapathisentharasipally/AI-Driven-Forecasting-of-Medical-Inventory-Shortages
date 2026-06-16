from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config.database import get_database
from app.core.exception_handler import NotFoundException, ValidationException
from app.core.permissions import INVENTORY_READ, INVENTORY_WRITE
from app.core.response_handler import created_response, paginated_response, success_response
from app.core.role_checker import RoleChecker
from app.schemas.prescription_schema import PrescriptionCreate, ReturnCreate
from ._route_utils import paging_params, safe_regex, serialize_doc, utc_now, validate_object_id

router = APIRouter()

async def _next(db, prefix):
    y = utc_now().year
    seq = await db["counters"].find_one_and_update({"_id": f"{prefix}-{y}"}, {"$inc": {"value": 1}}, upsert=True, return_document=True)
    return f"{prefix.upper()}-{y}-{seq['value']:04d}"

@router.post("/")
async def create_prescription(data: PrescriptionCreate, 
                              db: AsyncIOMotorDatabase = Depends(get_database), 
                              current_user: dict = Depends(RoleChecker([INVENTORY_WRITE]))):
    payload = data.model_dump(mode="json")
    payload.update({"prescription_no": await _next(db, "rx"), 
                    "status": "pending",
                    "created_by": current_user.get("id") or current_user.get("email"), 
                    "created_at": utc_now(), "updated_at": utc_now()})
    res = await db["prescriptions"].insert_one(payload)
    return created_response(serialize_doc(await db["prescriptions"].find_one({"_id": res.inserted_id})), "Prescription created successfully")

@router.get("/")
async def list_prescriptions(search: str | None = Query(None),
                            status: str | None = Query(None), 
                            page: int = Query(1, ge=1), 
                            limit: int = Query(20, ge=1, le=100), 
                            db: AsyncIOMotorDatabase = Depends(get_database), 
                            current_user: dict = Depends(RoleChecker([INVENTORY_READ]))):
    page, skip = paging_params(page, limit)
    query = {}
    if status: query["status"] = status
    rx = safe_regex(search)
    if rx: query["$or"] = [{"prescription_no": rx}, 
                        {"patient_name": rx}, 
                        {"items.medicine_name": rx}]
    total = await db["prescriptions"].count_documents(query)
    docs = await db["prescriptions"].find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    return paginated_response([serialize_doc(d) for d in docs], total, page, limit, "Prescriptions fetched successfully")

@router.patch("/{id}/dispense")
async def dispense_prescription(id: str, db: AsyncIOMotorDatabase = Depends(get_database), current_user: dict = Depends(RoleChecker([INVENTORY_WRITE]))):
    pres = await db["prescriptions"].find_one({"_id": validate_object_id(id)})
    if not pres: raise NotFoundException("Prescription not found")
    if pres.get("status") == "dispensed": raise ValidationException("Prescription is already dispensed")
    for item in pres.get("items", []):
        await db["inventory_items"].update_one({"_id": validate_object_id(item["inventory_item_id"], "inventory_item_id")}, {"$inc": {"current_stock": -item["quantity"], "stock_on_hand": -item["quantity"]}, "$set": {"updated_at": utc_now()}})
    dispensed = {"prescription_id": id, "prescription_no": pres.get("prescription_no"), "patient_name": pres.get("patient_name"), "items": pres.get("items", []), "dispensed_by": current_user.get("id") or current_user.get("email"), "dispensed_at": utc_now(), "created_at": utc_now()}
    await db["dispensed_items"].insert_one(dispensed)
    await db["prescriptions"].update_one({"_id": pres["_id"]}, {"$set": {"status": "dispensed", "dispensed_at": utc_now(), "updated_at": utc_now()}})
    return success_response(serialize_doc(await db["prescriptions"].find_one({"_id": pres["_id"]})), "Prescription dispensed successfully")

@router.get("/dispensed-items")
async def list_dispensed_items(page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100), db: AsyncIOMotorDatabase = Depends(get_database), current_user: dict = Depends(RoleChecker([INVENTORY_READ]))):
    page, skip = paging_params(page, limit)
    total = await db["dispensed_items"].count_documents({})
    docs = await db["dispensed_items"].find({}).sort("dispensed_at", -1).skip(skip).limit(limit).to_list(limit)
    return paginated_response([serialize_doc(d) for d in docs], total, page, limit, "Dispensed items fetched successfully")

@router.post("/returns")
async def create_return(data: ReturnCreate, db: AsyncIOMotorDatabase = Depends(get_database), current_user: dict = Depends(RoleChecker([INVENTORY_WRITE]))):
    payload = data.model_dump(mode="json")
    payload.update({"return_no": await _next(db, "rt"), "created_by": current_user.get("id") or current_user.get("email"), "created_at": utc_now()})
    res = await db["returns"].insert_one(payload)
    await db["inventory_items"].update_one({"_id": validate_object_id(payload["inventory_item_id"], "inventory_item_id")}, {"$inc": {"current_stock": payload["quantity"], "stock_on_hand": payload["quantity"]}, "$set": {"updated_at": utc_now()}})
    return created_response(serialize_doc(await db["returns"].find_one({"_id": res.inserted_id})), "Return created successfully")
