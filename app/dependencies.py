from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.database.session import SessionLocal
from app.repositories.unit_of_work import UnitOfWork
from app.services.auth_service import AuthService


def get_db_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_unit_of_work(
    session: Annotated[Session, Depends(get_db_session)],
) -> UnitOfWork:
    return UnitOfWork(session)


def get_auth_service(
    uow: Annotated[UnitOfWork, Depends(get_unit_of_work)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthService:
    return AuthService(
        uow=uow,
        secret_key=settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
        access_token_expire_minutes=(
            settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        ),
        refresh_token_expire_days=(
            settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        ),
    )
