import re
from fastapi import HTTPException, status
from passlib.context import CryptContext

from app.core.exception_handler import ValidationException

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 14

def hash_password(plain: str) -> str:
    validate_password_strength(plain)
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    validate_password_strength(plain)
    return pwd_context.verify(plain, hashed)


def validate_password_strength(password: str) -> bool:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters"
        )
    if len(password) > MAX_PASSWORD_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password cannot exceed 14 characters"
        )

    if not re.search(r"[A-Z]", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one uppercase letter"
        )

    if not re.search(r"\d", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one digit"
        )

    if not re.search(r"[^A-Za-z0-9]", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one special character"
        )

    return True