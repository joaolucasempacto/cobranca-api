from uuid import UUID

from app.exceptions.base import NotFoundError
from app.models.role import Role
from app.repositories.unit_of_work import UnitOfWork


class RoleService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def get_by_id(self, role_id: UUID) -> Role:
        role = self._uow.roles.get_by_id(role_id)
        if role is None:
            raise NotFoundError("Perfil não encontrado")
        return role
