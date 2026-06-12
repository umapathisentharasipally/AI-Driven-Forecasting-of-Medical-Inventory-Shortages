from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.user_schema import UserResponse


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse | None = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)

    @field_validator("new_password")
    @classmethod
    def new_password_must_differ(cls, value: str, info):
        old_password = info.data.get("old_password")
        if old_password and value == old_password:
            raise ValueError("New password must be different from old password")
        return value