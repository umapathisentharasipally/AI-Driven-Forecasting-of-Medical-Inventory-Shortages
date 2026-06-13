import asyncio

from fastapi import APIRouter, Depends, Request
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordRequestForm,
)
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config.database import get_database
from app.config.security import get_current_active_user
from app.core.response_handler import success_response
from app.schemas.auth_schema import ChangePasswordRequest, LoginRequest, RefreshTokenRequest
from app.services import auth_service
from app.services.audit_log_service import log_action
from app.services.user_service import to_user_response

router = APIRouter()
bearer_scheme = HTTPBearer()


@router.post("/login")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    data = LoginRequest(
        email=form_data.username,
        password=form_data.password,
    )

    token_response = await auth_service.login(db, data)

    if token_response.user is not None:
        asyncio.create_task(
            log_action(
                db=db,
                user_id=token_response.user.id,
                action="LOGIN",
                resource_type="user",
                resource_id=token_response.user.id,
                request=request,
            )
        )

    return {
        "access_token": token_response.access_token,
        "token_type": "bearer",
    }


@router.post("/refresh")
async def refresh(
    data: RefreshTokenRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    token_response = await auth_service.refresh_access_token(db, data)
    return success_response(
        data=token_response.model_dump(mode="json"),
        message="Access token refreshed successfully",
    )


@router.post("/logout")
async def logout(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    current_user: dict = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    await auth_service.logout(credentials.credentials)

    asyncio.create_task(
        log_action(
            db=db,
            user_id=str(current_user["_id"]),
            action="LOGOUT",
            resource_type="user",
            resource_id=str(current_user["_id"]),
            request=request,
        )
    )

    return success_response(message="Logged out successfully")


@router.post("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_active_user),
):
    await auth_service.change_password(db, str(current_user["_id"]), data)

    asyncio.create_task(
        log_action(
            db=db,
            user_id=str(current_user["_id"]),
            action="PASSWORD_CHANGE",
            resource_type="user",
            resource_id=str(current_user["_id"]),
        )
    )

    return success_response(message="Password changed successfully")


@router.get("/me")
async def me(
    current_user: dict = Depends(get_current_active_user),
):
    return success_response(
        data=to_user_response(current_user).model_dump(mode="json"),
        message="Current user fetched successfully",
    )