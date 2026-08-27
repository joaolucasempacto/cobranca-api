from types import TracebackType

from sqlalchemy.orm import Session

from app.repositories.customer_repository import CustomerRepository
from app.repositories.permission_repository import PermissionRepository
from app.repositories.revoked_token_repository import RevokedTokenRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository


class UnitOfWork:
    def __init__(self, session: Session) -> None:
        self._session = session
        self.customers = CustomerRepository(session)
        self.users = UserRepository(session)
        self.roles = RoleRepository(session)
        self.permissions = PermissionRepository(session)
        self.revoked_tokens = RevokedTokenRepository(session)

    def __enter__(self) -> "UnitOfWork":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            self.rollback()

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()
