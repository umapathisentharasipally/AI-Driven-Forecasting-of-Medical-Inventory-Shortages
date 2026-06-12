from datetime import timedelta
from typing import Any, Dict

from jose import JWTError, ExpiredSignatureError, jwt

from app.config.settings import settings
from app.core.exception_handler import UnauthorizedException
from app.utils.date_utils import utc_now


def create_access_token(data: dict) -> str:
    now = utc_now()
    payload = data.copy()
    payload.update(
        {
            "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            "iat": now,
            "type": "access",
        }
    )
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict) -> str:
    now = utc_now()
    payload = data.copy()
    payload.update(
        {
            "exp": now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            "iat": now,
            "type": "refresh",
        }
    )
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except ExpiredSignatureError as exc:
        raise UnauthorizedException("Token has expired") from exc
    except JWTError as exc:
        raise UnauthorizedException("Invalid token") from exc


def verify_token_type(payload: dict, expected: str) -> None:
    token_type = payload.get("type")
    if token_type != expected:
        raise UnauthorizedException(f"Invalid token type. Expected {expected}")