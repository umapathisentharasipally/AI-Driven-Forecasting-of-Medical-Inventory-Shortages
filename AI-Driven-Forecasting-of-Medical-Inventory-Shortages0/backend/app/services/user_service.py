from typing import List, Optional, Tuple

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exception_handler import ConflictException, ForbiddenException, NotFoundException
from app.core.password_handler import hash_password, validate_password_strength
from app.repositories import role_repository, user_repository
from app.schemas.user_schema import UserCreate, UserResponse, UserUpdate
from app.utils.date_utils import utc_now
from app.utils.validation_utils import validate_pagination


def to_user_response(user: dict) -> UserResponse:
    return UserResponse(
        id=str(user["_id"]),
        email=user["email"],
        full_name=user["full_name"],
        employee_id=user.get("employee_id"),
        role_id=str(user["role_id"]),
        role_name=user["role_name"],
        department=user.get("department"),
        is_active=user["is_active"],
        last_login=user.get("last_login"),
        created_at=user["created_at"],
        updated_at=user["updated_at"],
    )


async def create_user(
    db: AsyncIOMotorDatabase,
    data: UserCreate,
) -> UserResponse:
    existing = await user_repository.get_by_email(db, str(data.email))
    if existing:
        raise ConflictException("Email already exists")

    role = await role_repository.get_by_id(db, data.role_id)
    if not role:
        raise NotFoundException("Role not found")

    validate_password_strength(data.password)

    now = utc_now()
    user_doc = {
        "email": str(data.email),
        "password_hash": hash_password(data.password),
        "full_name": data.full_name,
        "employee_id": data.employee_id,
        "role_id": role["_id"],
        "role_name": role["name"],
        "department": data.department,
        "is_active": True,
        "last_login": None,
        "created_at": now,
        "updated_at": now,
    }

    created = await user_repository.create(db, user_doc)
    return to_user_response(created)


async def get_user(
    db: AsyncIOMotorDatabase,
    user_id: str,
) -> UserResponse:
    user = await user_repository.get_by_id(db, user_id)
    if not user:
        raise NotFoundException("User not found")
    return to_user_response(user)


async def list_users(
    db: AsyncIOMotorDatabase,
    page: int,
    limit: int,
    department: Optional[str],
    role_id: Optional[str],
    is_active: Optional[bool],
) -> Tuple[List[UserResponse], int]:
    page, limit = validate_pagination(page, limit)

    users, total = await user_repository.get_all(
        db=db,
        page=page,
        limit=limit,
        filters={
            "department": department,
            "role_id": role_id,
            "is_active": is_active,
        },
    )

    return [to_user_response(user) for user in users], total


async def update_user(
    db: AsyncIOMotorDatabase,
    user_id: str,
    data: UserUpdate,
) -> UserResponse:
    existing = await user_repository.get_by_id(db, user_id)
    if not existing:
        raise NotFoundException("User not found")

    update_data = data.model_dump(exclude_unset=True)

    updated = await user_repository.update(db, user_id, update_data)
    if not updated:
        raise NotFoundException("User not found")

    return to_user_response(updated)


async def deactivate_user(
    db: AsyncIOMotorDatabase,
    user_id: str,
    current_user_id: str,
) -> None:
    if user_id == current_user_id:
        raise ForbiddenException("You cannot deactivate your own account")

    existing = await user_repository.get_by_id(db, user_id)
    if not existing:
        raise NotFoundException("User not found")

    deleted = await user_repository.soft_delete(db, user_id)
    if not deleted:
        raise NotFoundException("User not found")