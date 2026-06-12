import asyncio
from typing import Set

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config.settings import settings
from app.core.exception_handler import NotFoundException, UnauthorizedException
from app.core.jwt_handler import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type,
)
from app.core.password_handler import (
    hash_password,
    validate_password_strength,
    verify_password,
)
from app.repositories import role_repository, user_repository
from app.schemas.auth_schema import ChangePasswordRequest, LoginRequest, RefreshTokenRequest, TokenResponse
from app.services.user_service import to_user_response

_token_blacklist: Set[str] = set()


async def login(
    db: AsyncIOMotorDatabase,
    data: LoginRequest,
) -> TokenResponse:
    email = str(data.email).lower().strip()
    user = await user_repository.get_by_email(db, email)    
    if not user:
        raise UnauthorizedException("Invalid email or password")

    if not verify_password(data.password, user["password_hash"]):
        raise UnauthorizedException("Invalid email or password")

    if not user.get("is_active", False):
        raise UnauthorizedException("User account is inactive")

    role = await role_repository.get_by_id(db, str(user["role_id"]))
    if not role:
        raise UnauthorizedException("User role is invalid")

    user["role_name"] = role["name"]

    await asyncio.create_task(user_repository.update_last_login(db, str(user["_id"])))

    token_payload = {
        "sub": str(user["_id"]),
        "email": user["email"],
        "role": role["name"],
        "permissions": role.get("permissions", []),
    }

    return TokenResponse(
        access_token=create_access_token(token_payload),
        refresh_token=create_refresh_token(token_payload),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=to_user_response(user),
    )


async def refresh_access_token(
    db: AsyncIOMotorDatabase,
    data: RefreshTokenRequest,
) -> TokenResponse:
    if is_token_blacklisted(data.refresh_token):
        raise UnauthorizedException("Refresh token has been revoked")

    payload = decode_token(data.refresh_token)
    verify_token_type(payload, "refresh")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException("Invalid refresh token")

    user = await user_repository.get_by_id(db, user_id)
    if not user:
        raise UnauthorizedException("User not found")

    if not user.get("is_active", False):
        raise UnauthorizedException("User account is inactive")

    role = await role_repository.get_by_id(db, str(user["role_id"]))
    if not role:
        raise UnauthorizedException("User role is invalid")

    user["role_name"] = role["name"]

    token_payload = {
        "sub": str(user["_id"]),
        "email": user["email"],
        "role": role["name"],
        "permissions": role.get("permissions", []),
    }

    return TokenResponse(
        access_token=create_access_token(token_payload),
        refresh_token=None,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=to_user_response(user),
    )


async def change_password(
    db: AsyncIOMotorDatabase,
    user_id: str,
    data: ChangePasswordRequest,
) -> None:
    user = await user_repository.get_by_id(db, user_id)
    if not user:
        raise NotFoundException("User not found")

    if not verify_password(data.old_password, user["password_hash"]):
        raise UnauthorizedException("Old password is incorrect")

    validate_password_strength(data.new_password)

    await user_repository.update(
        db=db,
        user_id=user_id,
        data={"password_hash": hash_password(data.new_password)},
    )


async def logout(token: str) -> None:
    _token_blacklist.add(token)


def is_token_blacklisted(token: str) -> bool:
    return token in _token_blacklist