from typing import Any, Dict

from bson import ObjectId
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config.database import get_database
from app.core.exception_handler import UnauthorizedException
from app.core.jwt_handler import decode_token, verify_token_type

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

UserDocument = Dict[str, Any]


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> UserDocument:
    payload = decode_token(token)
    verify_token_type(payload, "access")

    subject = payload.get("sub")
    if not subject:
        raise UnauthorizedException("Invalid authentication token")

    query: dict[str, Any]
    if ObjectId.is_valid(subject):
        query = {"_id": ObjectId(subject)}
    else:
        query = {"email": subject}

    user = await db["users"].find_one(query)
    if not user:
        raise UnauthorizedException("User not found or token is invalid")

    return user


async def get_current_active_user(
    current_user: UserDocument = Depends(get_current_user),
) -> UserDocument:
    if not current_user.get("is_active", False):
        raise UnauthorizedException("User account is inactive")
    return current_user