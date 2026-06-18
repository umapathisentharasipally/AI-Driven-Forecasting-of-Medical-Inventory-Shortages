from typing import Optional

from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config.database import get_database
from app.config.security import get_current_active_user
from app.core.permissions import USER_DELETE, USER_READ, USER_WRITE
from app.core.response_handler import created_response, paginated_response, success_response
from app.core.role_checker import RoleChecker
from app.schemas.user_schema import UserCreate, UserUpdate
from app.services import user_service

router = APIRouter()


@router.post("/")
async def create_user(
    data: UserCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([USER_WRITE])),
):
    user = await user_service.create_user(db, data)
    return created_response(
        data=user.model_dump(mode="json"),
        message="User created successfully",
    )


@router.get("/")
async def list_users(
    department: Optional[str] = Query(default=None),
    role_id: Optional[str] = Query(default=None),
    is_active: Optional[bool] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([USER_READ])),
):
    users, total = await user_service.list_users(
        db=db,
        page=page,
        limit=limit,
        department=department,
        role_id=role_id,
        is_active=is_active,
    )

    return paginated_response(
        data=[user.model_dump(mode="json") for user in users],
        total=total,
        page=page,
        limit=limit,
        message="Users fetched successfully",
    )


@router.get("/{user_id}")
async def get_user(
    user_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([USER_READ])),
):
    user = await user_service.get_user(db, user_id)
    return success_response(
        data=user.model_dump(mode="json"),
        message="User fetched successfully",
    )


@router.patch("/{user_id}")
async def update_user(
    user_id: str,
    data: UserUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([USER_WRITE])),
):
    user = await user_service.update_user(db, user_id, data)
    return success_response(
        data=user.model_dump(mode="json"),
        message="User updated successfully",
    )


@router.delete("/{user_id}")
async def deactivate_user(
    user_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([USER_DELETE])),
):
    await user_service.deactivate_user(
        db=db,
        user_id=user_id,
        current_user_id=str(current_user["_id"]),
    )
    return success_response(message="User deactivated successfully")