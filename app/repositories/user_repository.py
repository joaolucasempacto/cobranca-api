from uuid import UUID

from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session

from app.models.associations import role_permissions, user_roles
from app.models.permission import Permission
from app.models.role import Role
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

    def active_exists_by_id(self, user_id: UUID) -> bool:
        statement = select(User.id).where(
            User.id == user_id,
            User.is_active.is_(True),
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

    def has_permission(self, user_id: UUID, permission_code: str) -> bool:
        statement = (
            select(Permission.id)
            .select_from(user_roles)
            .join(Role, Role.id == user_roles.c.role_id)
            .join(role_permissions, role_permissions.c.role_id == Role.id)
            .join(
                Permission,
                Permission.id == role_permissions.c.permission_id,
            )
            .where(
                user_roles.c.user_id == user_id,
                Role.deleted_at.is_(None),
                Permission.code == permission_code,
                Permission.deleted_at.is_(None),
            )
        )
        return self._session.scalar(statement) is not None

    def list_roles(self, user_id: UUID) -> list[Role]:
        statement = (
            select(Role)
            .join(user_roles, user_roles.c.role_id == Role.id)
            .where(
                user_roles.c.user_id == user_id,
                Role.deleted_at.is_(None),
            )
            .order_by(Role.name.asc())
        )
        return list(self._session.scalars(statement).all())

    def has_role(self, user_id: UUID, role_id: UUID) -> bool:
        statement = select(user_roles.c.role_id).where(
            user_roles.c.user_id == user_id,
            user_roles.c.role_id == role_id,
        )
        return self._session.scalar(statement) is not None

    def add_role(self, user_id: UUID, role_id: UUID) -> None:
        self._session.execute(
            insert(user_roles).values(user_id=user_id, role_id=role_id)
        )
        self._session.flush()

    def remove_role(self, user_id: UUID, role_id: UUID) -> None:
        self._session.execute(
            delete(user_roles).where(
                user_roles.c.user_id == user_id,
                user_roles.c.role_id == role_id,
            )
        )
        self._session.flush()

    def list(self, offset: int, limit: int) -> list[User]:
        statement = (
            select(User)
            .where(User.deleted_at.is_(None))
            .order_by(User.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self._session.scalars(statement).all())

    def add(self, user: User) -> User:
        self._session.add(user)
        self._session.flush()
        return user
