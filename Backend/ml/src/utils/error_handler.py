from __future__ import annotations

from functools import wraps
from typing import Any, Callable, TypeVar

from .exceptions import MLProjectError
from .logger import get_logger, log_exception

F = TypeVar("F", bound=Callable[..., Any])


def log_and_raise(message: str, error_type: type[MLProjectError]) -> Callable[[F], F]:
    """Decorator for consistent exception handling in pipelines and CLI entrypoints."""
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger = get_logger(func.__module__)
            try:
                logger.info("Started: %s", func.__name__)
                result = func(*args, **kwargs)
                logger.info("Completed: %s", func.__name__)
                return result
            except MLProjectError:
                raise
            except Exception as exc:
                log_exception(logger, message, exc)
                raise error_type(message) from exc
        return wrapper  # type: ignore[return-value]
    return decorator
