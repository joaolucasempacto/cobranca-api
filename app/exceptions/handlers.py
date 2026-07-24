import logging

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.exceptions.base import (
    AppError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
)

logger = logging.getLogger(__name__)

_STATUS_MAP = {
    NotFoundError: status.HTTP_404_NOT_FOUND,
    ConflictError: status.HTTP_409_CONFLICT,
    UnauthorizedError: status.HTTP_401_UNAUTHORIZED,
    ForbiddenError: status.HTTP_403_FORBIDDEN,
}


def _get_status_code(exc: AppError) -> int:
    for exception_type, status_code in _STATUS_MAP.items():
        if isinstance(exc, exception_type):
            return status_code

    return status.HTTP_400_BAD_REQUEST


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    status_code = _get_status_code(exc)

    logger.warning(
        "Erro de aplicação: %s | path=%s",
        exc.message,
        request.url.path,
    )

    return JSONResponse(
        status_code=status_code,
        content={"detail": exc.message},
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    logger.error(
        "Erro não tratado: %s | path=%s",
        str(exc),
        request.url.path,
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Erro interno do servidor"},
    )