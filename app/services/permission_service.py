from uuid import UUID

from app.exceptions.base import NotFoundError
from app.models.permission import Permission
from app.repositories.unit_of_work import UnitOfWork


class PermissionService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

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
