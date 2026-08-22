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

    def list_users(self, offset: int, limit: int) -> list[User]:
        return self._uow.users.list(offset=offset, limit=limit)

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

    def update(
        self,
        user_id: UUID,
        *,
        email: str | None = None,
        password: str | None = None,
        is_active: bool | None = None,
    ) -> User:
        user = self.get_by_id(user_id)

        if email is not None and email != user.email:
            if self._uow.users.exists_by_email(email):
                raise ConflictError("E-mail já cadastrado")
            user.email = email

        if password is not None:
            user.password_hash = hash_password(password)

        if is_active is not None:
            user.is_active = is_active

        self._uow.commit()
        return user

    def delete(self, user_id: UUID) -> None:
        user = self.get_by_id(user_id)
        user.soft_delete()
        self._uow.commit()

    def add(self, user: User) -> User:
        added_user = self._uow.users.add(user)
        self._uow.commit()
        return added_user
