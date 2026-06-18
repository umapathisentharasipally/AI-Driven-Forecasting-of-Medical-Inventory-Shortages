from math import ceil
from typing import Any

from fastapi import Response
from fastapi.responses import JSONResponse

from app.utils.date_utils import utc_now


def success_response(
    data: Any = None,
    message: str = "Success",
    status_code: int = 200,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": data,
            "timestamp": utc_now().isoformat(),
        },
    )


def paginated_response(
    data: Any,
    total: int,
    page: int,
    limit: int,
    message: str = "Success",
) -> JSONResponse:
    pages = ceil(total / limit) if limit else 0

    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "message": message,
            "data": data,
            "meta": {
                "total": total,
                "page": page,
                "limit": limit,
                "pages": pages,
                "has_next": page < pages,
                "has_prev": page > 1,
            },
            "timestamp": utc_now().isoformat(),
        },
    )


def created_response(data: Any = None, message: str = "Created") -> JSONResponse:
    return success_response(data=data, message=message, status_code=201)


def no_content_response() -> Response:
    return Response(status_code=204)