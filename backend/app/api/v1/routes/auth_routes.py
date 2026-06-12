import asyncio

from fastapi import APIRouter, Depends, Request
from app.services.audit_log_service import log_action
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config.database import get_database
from app.config.security import get_current_active_user
from app.core.response_handler import success_response
from app.schemas.auth_schema import ChangePasswordRequest, LoginRequest, RefreshTokenRequest
from app.services import auth_service
from app.services.audit_log_service import log_action
from app.services.user_service import to_user_response

router = APIRouter()
#logger = get_logger(__name__)
bearer_scheme = HTTPBearer()



#async def audit_auth_stub(action: str, email: str | None = None, user_id: str | None = None) -> None:
    #logger.info(
        #"auth_audit_event",
        #action=action,
        #email=email,
        #user_id=user_id,
   # )


@router.post("/login")
async def login(
    data: LoginRequest,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
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

    return success_response(
        data=token_response.model_dump(mode="json"),
        message="Login successful",
    )


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