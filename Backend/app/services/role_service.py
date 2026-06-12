from typing import List

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exception_handler import ConflictException, NotFoundException
from app.repositories import role_repository
from app.schemas.role_schema import RoleCreate, RoleResponse, RoleUpdate
from app.utils.date_utils import utc_now


def to_role_response(role: dict) -> RoleResponse:
    return RoleResponse(
        id=str(role["_id"]),
        name=role["name"],
        permissions=role["permissions"],
        description=role.get("description"),
        created_at=role["created_at"],
    )


async def create_role(
    db: AsyncIOMotorDatabase,
    data: RoleCreate,
) -> RoleResponse:
    existing = await role_repository.get_by_name(db, data.name)
    if existing:
        raise ConflictException("Role name already exists")

    role_doc = {
        "name": data.name,
        "permissions": data.permissions,
        "description": data.description,
        "created_at": utc_now(),
    }

    created = await role_repository.create(db, role_doc)
    return to_role_response(created)


async def get_role(
    db: AsyncIOMotorDatabase,
    role_id: str,
) -> RoleResponse:
    role = await role_repository.get_by_id(db, role_id)
    if not role:
        raise NotFoundException("Role not found")
    return to_role_response(role)


async def list_roles(db: AsyncIOMotorDatabase) -> List[RoleResponse]:
    roles = await role_repository.get_all(db)
    return [to_role_response(role) for role in roles]


async def update_role(
    db: AsyncIOMotorDatabase,
    role_id: str,
    data: RoleUpdate,
) -> RoleResponse:
    existing = await role_repository.get_by_id(db, role_id)
    if not existing:
        raise NotFoundException("Role not found")

    update_data = data.model_dump(exclude_unset=True)

    updated = await role_repository.update(db, role_id, update_data)
    if not updated:
        raise NotFoundException("Role not found")

    return to_role_response(updated)


async def delete_role(
    db: AsyncIOMotorDatabase,
    role_id: str,
) -> None:
    existing = await role_repository.get_by_id(db, role_id)
    if not existing:
        raise NotFoundException("Role not found")

    deleted = await role_repository.delete(db, role_id)
    if not deleted:
        raise NotFoundException("Role not found")