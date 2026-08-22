from uuid import UUID

from app.exceptions.base import ConflictError, NotFoundError
from app.models.permission import Permission
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

    def update(
        self,
        role_id: UUID,
        name: str | None = None,
        description: str | None = None,
    ) -> Role:
        role = self.get_by_id(role_id)
        if (
            name is not None
            and name != role.name
            and self._uow.roles.exists_by_name(name)
        ):
            raise ConflictError("Perfil já cadastrado")

        role.update_details(name=name, description=description)
        self._uow.commit()
        return role

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

    def list_permissions(self, role_id: UUID) -> list[Permission]:
        self.get_by_id(role_id)
        return self._uow.roles.list_permissions(role_id)

    def grant_permission(
        self,
        role_id: UUID,
        permission_id: UUID,
    ) -> None:
        self.get_by_id(role_id)
        if self._uow.permissions.get_by_id(permission_id) is None:
            raise NotFoundError("Permissão não encontrada")
        if self._uow.roles.has_permission(role_id, permission_id):
            raise ConflictError("Permissão já atribuída ao perfil")

        self._uow.roles.add_permission(role_id, permission_id)
        self._uow.commit()

    def revoke_permission(
        self,
        role_id: UUID,
        permission_id: UUID,
    ) -> None:
        self.get_by_id(role_id)
        if self._uow.permissions.get_by_id(permission_id) is None:
            raise NotFoundError("Permissão não encontrada")
        if not self._uow.roles.has_permission(role_id, permission_id):
            raise NotFoundError("Permissão não atribuída ao perfil")

        self._uow.roles.remove_permission(role_id, permission_id)
        self._uow.commit()

    def add(self, role: Role) -> Role:
        added_role = self._uow.roles.add(role)
        self._uow.commit()
        return added_role
