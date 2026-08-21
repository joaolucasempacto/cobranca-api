from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.role import Role


class RoleRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, role_id: UUID) -> Role | None:
        statement = select(Role).where(
            Role.id == role_id,
            Role.deleted_at.is_(None),
        )
        return self._session.scalar(statement)

    def get_by_name(self, name: str) -> Role | None:
        statement = select(Role).where(
            Role.name == name,
            Role.deleted_at.is_(None),
        )
        return self._session.scalar(statement)

    def exists_by_name(self, name: str) -> bool:
        statement = select(Role.id).where(
            Role.name == name,
            Role.deleted_at.is_(None),
        )
        return self._session.scalar(statement) is not None

    def add(self, role: Role) -> Role:
        self._session.add(role)
        self._session.flush()
        return role
