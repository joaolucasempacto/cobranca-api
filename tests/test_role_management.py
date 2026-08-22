from datetime import datetime, timezone
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock
from uuid import uuid4

from app.exceptions.base import ConflictError
from app.routers.roles import create_role, list_roles, router
from app.schemas.role import RoleCreate
from app.services.role_service import RoleService


class RoleManagementTests(TestCase):
    def test_create_role_rejects_duplicate_name(self) -> None:
        uow = Mock()
        uow.roles.exists_by_name.return_value = True

        with self.assertRaisesRegex(ConflictError, "Perfil já cadastrado"):
            RoleService(uow).create("admin", "Administradores")

        uow.roles.add.assert_not_called()
        uow.commit.assert_not_called()

    def test_create_role_persists_and_commits(self) -> None:
        uow = Mock()
        uow.roles.exists_by_name.return_value = False
        created = Mock()
        uow.roles.add.return_value = created

        result = RoleService(uow).create("admin", "Administradores")

        self.assertIs(result, created)
        role = uow.roles.add.call_args.args[0]
        self.assertEqual(role.name, "admin")
        self.assertEqual(role.description, "Administradores")
        uow.commit.assert_called_once_with()

    def test_list_roles_delegates_pagination(self) -> None:
        uow = Mock()
        expected = [Mock(), Mock()]
        uow.roles.list.return_value = expected

        result = RoleService(uow).list_roles(offset=10, limit=25)

        self.assertEqual(result, expected)
        uow.roles.list.assert_called_once_with(offset=10, limit=25)

    def test_router_delegates_create_and_list(self) -> None:
        now = datetime.now(timezone.utc)
        role = SimpleNamespace(
            id=uuid4(),
            name="admin",
            description="Administradores",
            created_at=now,
            updated_at=now,
        )
        service = Mock()
        service.create.return_value = role
        service.list_roles.return_value = [role]

        created = create_role(
            RoleCreate(name="admin", description="Administradores"),
            service,
            Mock(),
        )
        listed = list_roles(service, Mock(), offset=0, limit=50)

        self.assertEqual(created.name, "admin")
        self.assertEqual([item.name for item in listed], ["admin"])
        service.create.assert_called_once_with(
            name="admin",
            description="Administradores",
        )
        service.list_roles.assert_called_once_with(offset=0, limit=50)

    def test_router_exposes_role_management_routes(self) -> None:
        routes = {
            (route.path, tuple(sorted(route.methods or set())))
            for route in router.routes
        }

        self.assertIn(("/roles", ("GET",)), routes)
        self.assertIn(("/roles", ("POST",)), routes)
