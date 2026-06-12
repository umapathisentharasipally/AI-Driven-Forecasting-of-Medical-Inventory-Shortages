from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.config.database import get_database
from app.core.permissions import ADMIN_ALL
from app.core.response_handler import created_response, success_response
from app.core.role_checker import RoleChecker
from app.schemas.role_schema import RoleCreate, RoleUpdate
from app.services import role_service

router = APIRouter()


@router.post("/")
async def create_role(
    data: RoleCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([ADMIN_ALL])),
):
    role = await role_service.create_role(db, data)
    return created_response(
        data=role.model_dump(mode="json"),
        message="Role created successfully",
    )


@router.get("/")
async def list_roles(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([ADMIN_ALL])),
):
    roles = await role_service.list_roles(db)
    return success_response(
        data=[role.model_dump(mode="json") for role in roles],
        message="Roles fetched successfully",
    )


@router.get("/{role_id}")
async def get_role(
    role_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([ADMIN_ALL])),
):
    role = await role_service.get_role(db, role_id)
    return success_response(
        data=role.model_dump(mode="json"),
        message="Role fetched successfully",
    )


@router.patch("/{role_id}")
async def update_role(
    role_id: str,
    data: RoleUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([ADMIN_ALL])),
):
    role = await role_service.update_role(db, role_id, data)
    return success_response(
        data=role.model_dump(mode="json"),
        message="Role updated successfully",
    )


@router.delete("/{role_id}")
async def delete_role(
    role_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([ADMIN_ALL])),
):
    await role_service.delete_role(db, role_id)
    return success_response(message="Role deleted successfully")