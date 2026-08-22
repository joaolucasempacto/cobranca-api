from uuid import UUID

from app.exceptions.base import ConflictError, NotFoundError
from app.models.role import Role
from app.repositories.unit_of_work import UnitOfWork


class RoleService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def list_roles(self, offset: int, limit: int) -> list[Role]:
        return self._uow.roles.list(offset=offset, limit=limit)

    def create(self, name: str, description: str | None = None) -> Role:
        if self._uow.roles.exists_by_name(name):
            raise ConflictError("Perfil já cadastrado")

        role = Role(name=name, description=description)
        added_role = self._uow.roles.add(role)
        self._uow.commit()
        return added_role

    def get_by_id(self, role_id: UUID) -> Role:
        role = self._uow.roles.get_by_id(role_id)
        if role is None:
            raise NotFoundError("Perfil não encontrado")
        return role

    def get_by_name(self, name: str) -> Role:
        role = self._uow.roles.get_by_name(name)
        if role is None:
            raise NotFoundError("Perfil não encontrado")
        return role

    def role_exists(self, name: str) -> bool:
        return self._uow.roles.exists_by_name(name)

    def add(self, role: Role) -> Role:
        added_role = self._uow.roles.add(role)
        self._uow.commit()
        return added_role
