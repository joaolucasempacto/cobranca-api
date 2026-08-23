from app.core.security import hash_password
from app.exceptions.base import ConflictError
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User
from app.repositories.unit_of_work import UnitOfWork

ADMIN_ROLE_NAME = "admin"
ADMIN_ROLE_DESCRIPTION = "Administrador do sistema"
ADMIN_PERMISSIONS: tuple[tuple[str, str], ...] = (
    ("users:read", "Consultar usuários"),
    ("users:write", "Gerenciar usuários"),
    ("roles:read", "Consultar perfis"),
    ("roles:write", "Gerenciar perfis"),
    ("permissions:read", "Consultar permissões"),
    ("permissions:write", "Gerenciar permissões"),
)


class BootstrapService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def bootstrap_admin(self, email: str, password: str) -> User:
        permissions = [
            self._get_or_create_permission(code, description)
            for code, description in ADMIN_PERMISSIONS
        ]
        role = self._get_or_create_admin_role()

        for permission in permissions:
            if not self._uow.roles.has_permission(role.id, permission.id):
                self._uow.roles.add_permission(role.id, permission.id)

        user = self._get_or_create_user(email, password)
        if not user.is_active:
            raise ConflictError("Usuário administrador está inativo")

        if not self._uow.users.has_role(user.id, role.id):
            self._uow.users.add_role(user.id, role.id)

        self._uow.commit()
        return user

    def _get_or_create_permission(
        self,
        code: str,
        description: str,
    ) -> Permission:
        permission = self._uow.permissions.get_by_code(code)
        if permission is not None:
            return permission
        if self._uow.permissions.exists_by_code(code):
            raise ConflictError(
                f"Permissão {code} existe, mas está removida logicamente"
            )
        return self._uow.permissions.add(
            Permission(code=code, description=description)
        )

    def _get_or_create_admin_role(self) -> Role:
        role = self._uow.roles.get_by_name(ADMIN_ROLE_NAME)
        if role is not None:
            return role
        if self._uow.roles.exists_by_name(ADMIN_ROLE_NAME):
            raise ConflictError(
                "Perfil admin existe, mas está removido logicamente"
            )
        return self._uow.roles.add(
            Role(
                name=ADMIN_ROLE_NAME,
                description=ADMIN_ROLE_DESCRIPTION,
            )
        )

    def _get_or_create_user(self, email: str, password: str) -> User:
        user = self._uow.users.get_by_email(email)
        if user is not None:
            return user
        if self._uow.users.exists_by_email(email):
            raise ConflictError(
                "E-mail do administrador existe, mas está removido logicamente"
            )
        return self._uow.users.add(
            User(
                email=email,
                password_hash=hash_password(password),
                is_active=True,
            )
        )
