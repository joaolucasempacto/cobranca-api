from collections.abc import Callable, Generator
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.database.session import SessionLocal
from app.exceptions.base import UnauthorizedError
from app.models.user import User
from app.repositories.unit_of_work import UnitOfWork
from app.services.auth_service import AuthService
from app.services.authorization_service import AuthorizationService
from app.services.user_service import UserService

bearer_scheme = HTTPBearer(auto_error=False)


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
        access_token_expire_minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
        refresh_token_expire_days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS,
    )


def get_authorization_service(
    uow: Annotated[UnitOfWork, Depends(get_unit_of_work)],
) -> AuthorizationService:
    return AuthorizationService(uow)


def get_user_service(
    uow: Annotated[UnitOfWork, Depends(get_unit_of_work)],
) -> UserService:
    return UserService(uow)


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError("Token de acesso ausente")
    return auth_service.authenticate_access_token(credentials.credentials)


def require_permission(permission_code: str) -> Callable[..., User]:
    def dependency(
        current_user: Annotated[User, Depends(get_current_user)],
        authorization_service: Annotated[
            AuthorizationService,
            Depends(get_authorization_service),
        ],
    ) -> User:
        authorization_service.require_permission(
            current_user.id,
            permission_code,
        )
        return current_user

    return dependency
