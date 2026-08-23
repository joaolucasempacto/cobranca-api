from uuid import UUID

from app.exceptions.base import ConflictError, NotFoundError
from app.models.permission import Permission
from app.repositories.unit_of_work import UnitOfWork


class PermissionService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def list_permissions(self, offset: int, limit: int) -> list[Permission]:
        return self._uow.permissions.list(offset=offset, limit=limit)

    def create(
        self,
        code: str,
        description: str | None = None,
    ) -> Permission:
        if self._uow.permissions.exists_by_code(code):
            raise ConflictError("Permissão já cadastrada")

        permission = Permission(code=code, description=description)
        added_permission = self._uow.permissions.add(permission)
        self._uow.commit()
        return added_permission

    def update(
        self,
        permission_id: UUID,
        code: str | None = None,
        description: str | None = None,
    ) -> Permission:
        permission = self.get_by_id(permission_id)
        if (
            code is not None
            and code != permission.code
            and self._uow.permissions.exists_by_code(code)
        ):
            raise ConflictError("Permissão já cadastrada")

        permission.update_details(
            code=code,
            description=description,
        )
        self._uow.commit()
        return permission

    def delete(self, permission_id: UUID) -> None:
        permission = self.get_by_id(permission_id)
        permission.soft_delete()
        self._uow.commit()

    def get_by_id(self, permission_id: UUID) -> Permission:
        permission = self._uow.permissions.get_by_id(permission_id)
        if permission is None:
            raise NotFoundError("Permissão não encontrada")
        return permission

    def get_by_code(self, code: str) -> Permission:
        permission = self._uow.permissions.get_by_code(code)
        if permission is None:
            raise NotFoundError("Permissão não encontrada")
        return permission

    def permission_exists(self, code: str) -> bool:
        return self._uow.permissions.exists_by_code(code)

    def add(self, permission: Permission) -> Permission:
        added_permission = self._uow.permissions.add(permission)
        self._uow.commit()
        return added_permission
