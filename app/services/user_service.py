from uuid import UUID

from app.core.security import hash_password
from app.exceptions.base import ConflictError, NotFoundError
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

    def user_exists(self, user_id: UUID) -> bool:
        return self._uow.users.exists_by_id(user_id)

    def active_user_exists(self, user_id: UUID) -> bool:
        return self._uow.users.active_exists_by_id(user_id)

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

    def active_email_exists(self, email: str) -> bool:
        return self._uow.users.active_exists_by_email(email)

    def create(
        self,
        email: str,
        password: str,
        is_active: bool = True,
    ) -> User:
        if self._uow.users.exists_by_email(email):
            raise ConflictError("E-mail já cadastrado")

        user = User(
            email=email,
            password_hash=hash_password(password),
            is_active=is_active,
        )
        added_user = self._uow.users.add(user)
        self._uow.commit()
        return added_user

    def add(self, user: User) -> User:
        added_user = self._uow.users.add(user)
        self._uow.commit()
        return added_user
