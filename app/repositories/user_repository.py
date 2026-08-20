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

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(
            User.email == email,
            User.deleted_at.is_(None),
        )
        return self._session.scalar(statement)

    def add(self, user: User) -> User:
        self._session.add(user)
        self._session.flush()
        return user
