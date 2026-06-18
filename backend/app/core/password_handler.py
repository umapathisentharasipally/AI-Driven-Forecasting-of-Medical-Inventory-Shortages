import re

from passlib.context import CryptContext

from app.core.exception_handler import ValidationException

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def validate_password_strength(password: str) -> bool:
    if len(password) < 8:
        raise ValidationException("Password must be at least 8 characters long")

    if not re.search(r"[A-Z]", password):
        raise ValidationException("Password must contain at least one uppercase letter")

    if not re.search(r"\d", password):
        raise ValidationException("Password must contain at least one digit")

    if not re.search(r"[^A-Za-z0-9]", password):
        raise ValidationException("Password must contain at least one special character")

    return True