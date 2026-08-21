from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, user_id: UUID) -> User | None:
        statement = select(User).where(
            User.id == user_id,
            User.deleted_at.is_(None),
        )
        return self._session.scalar(statement)

    def get_active_by_id(self, user_id: UUID) -> User | None:
        statement = select(User).where(
            User.id == user_id,
            User.is_active.is_(True),
            User.deleted_at.is_(None),
        )
        return self._session.scalar(statement)

    def exists_by_id(self, user_id: UUID) -> bool:
        statement = select(User.id).where(
            User.id == user_id,
            User.deleted_at.is_(None),
        )
        return self._session.scalar(statement) is not None

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(
            User.email == email,
            User.deleted_at.is_(None),
        )
        return self._session.scalar(statement)

    def get_active_by_email(self, email: str) -> User | None:
        statement = select(User).where(
            User.email == email,
            User.is_active.is_(True),
            User.deleted_at.is_(None),
        )
        return self._session.scalar(statement)

    def exists_by_email(self, email: str) -> bool:
        statement = select(User.id).where(
            User.email == email,
            User.deleted_at.is_(None),
        )
        return self._session.scalar(statement) is not None

    def active_exists_by_email(self, email: str) -> bool:
        statement = select(User.id).where(
            User.email == email,
            User.is_active.is_(True),
            User.deleted_at.is_(None),
        )
        return self._session.scalar(statement) is not None

    def add(self, user: User) -> User:
        self._session.add(user)
        self._session.flush()
        return user
