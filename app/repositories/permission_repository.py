from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.permission import Permission


class PermissionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, permission_id: UUID) -> Permission | None:
        statement = select(Permission).where(
            Permission.id == permission_id,
            Permission.deleted_at.is_(None),
        )
        return self._session.scalar(statement)

    def get_by_code(self, code: str) -> Permission | None:
        statement = select(Permission).where(
            Permission.code == code,
            Permission.deleted_at.is_(None),
        )
        return self._session.scalar(statement)

    def add(self, permission: Permission) -> Permission:
        self._session.add(permission)
        self._session.flush()
        return permission
