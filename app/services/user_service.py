from uuid import UUID

from app.exceptions.base import NotFoundError
from app.models.user import User
from app.repositories.unit_of_work import UnitOfWork


class UserService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def get_by_id(self, user_id: UUID) -> User:
        user = self._uow.users.get_by_id(user_id)
        if user is None:
            raise NotFoundError("Usuário não encontrado")
        return user

    def get_active_by_id(self, user_id: UUID) -> User:
        user = self._uow.users.get_active_by_id(user_id)
        if user is None:
            raise NotFoundError("Usuário ativo não encontrado")
        return user

    def get_by_email(self, email: str) -> User:
        user = self._uow.users.get_by_email(email)
        if user is None:
            raise NotFoundError("Usuário não encontrado")
        return user

    def get_active_by_email(self, email: str) -> User:
        user = self._uow.users.get_active_by_email(email)
        if user is None:
            raise NotFoundError("Usuário ativo não encontrado")
        return user

    def email_exists(self, email: str) -> bool:
        return self._uow.users.exists_by_email(email)
