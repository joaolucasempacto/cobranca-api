import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.core.logging import setup_logging
from app.database.session import engine
from app.exceptions.base import AppError
from app.exceptions.handlers import (
    app_error_handler,
    unhandled_exception_handler,
)
from app.routers.auth import router as auth_router
from app.routers.charges import router as charges_router
from app.routers.customers import router as customers_router
from app.routers.health import router as health_router
from app.routers.permissions import router as permissions_router
from app.routers.roles import router as roles_router
from app.routers.users import router as users_router

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    logger.info("Inicializando aplicação")

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        logger.info("Conexão com o banco de dados validada")
        yield
    finally:
        engine.dispose()
        logger.info("Recursos do banco de dados liberados")


app = FastAPI(lifespan=lifespan)

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(
    health_router,
    prefix="/api/v1",
)
app.include_router(
    auth_router,
    prefix="/api/v1",
)
app.include_router(
    users_router,
    prefix="/api/v1",
)
app.include_router(
    customers_router,
    prefix="/api/v1",
)
app.include_router(
    charges_router,
    prefix="/api/v1",
)
app.include_router(
    roles_router,
    prefix="/api/v1",
)
app.include_router(
    permissions_router,
    prefix="/api/v1",
)
