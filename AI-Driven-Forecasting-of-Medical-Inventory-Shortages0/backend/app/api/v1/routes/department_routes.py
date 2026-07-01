from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING

from app.config.database import get_database
from app.core.exception_handler import ConflictException, NotFoundException
from app.core.permissions import ADMIN_ALL, INVENTORY_READ, INVENTORY_WRITE
from app.core.response_handler import created_response, paginated_response, success_response
from app.core.role_checker import RoleChecker
from app.schemas.department_schema import DepartmentCreate, DepartmentUpdate
from ._route_utils import paging_params, safe_regex, serialize_doc, utc_now, validate_object_id

router = APIRouter()

@router.on_event("startup")
async def _ensure_indexes():
    db = await get_database()
    await db["departments"].create_index([("code", ASCENDING)], unique=True)
    await db["departments"].create_index([("name", ASCENDING)])

@router.post("/")
async def create_department(data: DepartmentCreate, 
                            db: AsyncIOMotorDatabase = Depends(get_database), 
                            current_user: dict = Depends(RoleChecker([ADMIN_ALL]))):
    payload = data.model_dump()
    payload.update({"created_at": utc_now(), "updated_at": utc_now()})
    try:
        res = await db["departments"].insert_one(payload)
    except Exception as exc:
        if "duplicate" in str(exc).lower():
            raise ConflictException("Department code already exists")
        raise
    doc = await db["departments"].find_one({"_id": res.inserted_id})
    return created_response(serialize_doc(doc), "Department created successfully")

@router.get("/")
async def list_departments(search: str | None = Query(None), 
                           is_active: bool | None = Query(None), 
                           page: int = Query(1, ge=1), 
                           limit: int = Query(20, ge=1, le=100), 
                           db: AsyncIOMotorDatabase = Depends(get_database), 
                           current_user: dict = Depends(RoleChecker([INVENTORY_READ]))):
    page, skip = paging_params(page, limit)
    query = {}
    if is_active is not None:
        query["is_active"] = is_active
    rx = safe_regex(search)
    if rx:
        query["$or"] = [{"name": rx}, {"code": rx}, {"manager_name": rx}, {"code": rx}]
    total = await db["departments"].count_documents(query)
    docs = await db["departments"].find(query).sort("name", 1).skip(skip).limit(limit).to_list(limit)
    return paginated_response([serialize_doc(d) for d in docs], total, page, limit, "Departments fetched successfully")

@router.get("/{id}")
async def get_department(id: str, 
                         db: AsyncIOMotorDatabase = Depends(get_database), 
                         current_user: dict = Depends(RoleChecker([INVENTORY_READ]))):
    doc = await db["departments"].find_one({"_id": validate_object_id(id)})
    if not doc:
        raise NotFoundException("Department not found")
    return success_response(serialize_doc(doc), "Department fetched successfully")

@router.patch("/{id}")
async def update_department(id: str, 
                            data: DepartmentUpdate, 
                            db: AsyncIOMotorDatabase = Depends(get_database), 
                            current_user: dict = Depends(RoleChecker([ADMIN_ALL]))):
    payload = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
    payload["updated_at"] = utc_now()
    res = await db["departments"].update_one({"_id": validate_object_id(id)}, {"$set": payload})
    if res.matched_count == 0:
        raise NotFoundException("Department not found")
    return success_response(serialize_doc(await db["departments"].find_one({"_id": validate_object_id(id)})), "Department updated successfully")

@router.delete("/{id}")
async def deactivate_department(id: str, 
                                db: AsyncIOMotorDatabase = Depends(get_database), 
                                current_user: dict = Depends(RoleChecker([ADMIN_ALL]))):
    res = await db["departments"].update_one({"_id": validate_object_id(id)}, {"$set": {"is_active": False, "updated_at": utc_now()}})
    if res.matched_count == 0:
        raise NotFoundException("Department not found")
    return success_response(message="Department deactivated successfully")
