from uuid import UUID

from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session

from app.models.associations import role_permissions
from app.models.permission import Permission
from app.models.role import Role


class RoleRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list(self, offset: int, limit: int) -> list[Role]:
        statement = (
            select(Role)
            .where(Role.deleted_at.is_(None))
            .order_by(Role.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self._session.scalars(statement).all())

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
        statement = select(Role.id).where(Role.name == name)
        return self._session.scalar(statement) is not None

    def list_permissions(self, role_id: UUID) -> list[Permission]:
        statement = (
            select(Permission)
            .join(
                role_permissions,
                role_permissions.c.permission_id == Permission.id,
            )
            .where(
                role_permissions.c.role_id == role_id,
                Permission.deleted_at.is_(None),
            )
            .order_by(Permission.code.asc())
        )
        return list(self._session.scalars(statement).all())

    def has_permission(
        self,
        role_id: UUID,
        permission_id: UUID,
    ) -> bool:
        statement = select(role_permissions.c.permission_id).where(
            role_permissions.c.role_id == role_id,
            role_permissions.c.permission_id == permission_id,
        )
        return self._session.scalar(statement) is not None

    def add_permission(
        self,
        role_id: UUID,
        permission_id: UUID,
    ) -> None:
        self._session.execute(
            insert(role_permissions).values(
                role_id=role_id,
                permission_id=permission_id,
            )
        )
        self._session.flush()

    def remove_permission(
        self,
        role_id: UUID,
        permission_id: UUID,
    ) -> None:
        self._session.execute(
            delete(role_permissions).where(
                role_permissions.c.role_id == role_id,
                role_permissions.c.permission_id == permission_id,
            )
        )
        self._session.flush()

    def add(self, role: Role) -> Role:
        self._session.add(role)
        self._session.flush()
        return role
