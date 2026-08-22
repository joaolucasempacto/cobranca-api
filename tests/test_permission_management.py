from datetime import datetime, timezone
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock
from uuid import uuid4

from app.exceptions.base import ConflictError
from app.routers.permissions import (
    create_permission,
    list_permissions,
    router,
)
from app.schemas.permission import PermissionCreate
from app.services.permission_service import PermissionService


class PermissionManagementTests(TestCase):
    def test_create_permission_rejects_duplicate_code(self) -> None:
        uow = Mock()
        uow.permissions.exists_by_code.return_value = True

        with self.assertRaisesRegex(
            ConflictError,
            "Permissão já cadastrada",
        ):
            PermissionService(uow).create(
                "users:read",
                "Ler usuários",
            )

        uow.permissions.add.assert_not_called()
        uow.commit.assert_not_called()

    def test_create_permission_persists_and_commits(self) -> None:
        uow = Mock()
        uow.permissions.exists_by_code.return_value = False
        created = Mock()
        uow.permissions.add.return_value = created

        result = PermissionService(uow).create(
            "users:read",
            "Ler usuários",
        )

        self.assertIs(result, created)
        permission = uow.permissions.add.call_args.args[0]
        self.assertEqual(permission.code, "users:read")
        self.assertEqual(permission.description, "Ler usuários")
        uow.commit.assert_called_once_with()

    def test_list_permissions_delegates_pagination(self) -> None:
        uow = Mock()
        expected = [Mock(), Mock()]
        uow.permissions.list.return_value = expected

        result = PermissionService(uow).list_permissions(
            offset=10,
            limit=25,
        )

        self.assertEqual(result, expected)
        uow.permissions.list.assert_called_once_with(
            offset=10,
            limit=25,
        )

    def test_router_delegates_create_and_list(self) -> None:
        now = datetime.now(timezone.utc)
        permission = SimpleNamespace(
            id=uuid4(),
            code="users:read",
            description="Ler usuários",
            created_at=now,
            updated_at=now,
        )
        service = Mock()
        service.create.return_value = permission
        service.list_permissions.return_value = [permission]

        created = create_permission(
            PermissionCreate(
                code="users:read",
                description="Ler usuários",
            ),
            service,
            Mock(),
        )
        listed = list_permissions(
            service,
            Mock(),
            offset=0,
            limit=50,
        )

        self.assertEqual(created.code, "users:read")
        self.assertEqual(
            [item.code for item in listed],
            ["users:read"],
        )
        service.create.assert_called_once_with(
            code="users:read",
            description="Ler usuários",
        )
        service.list_permissions.assert_called_once_with(
            offset=0,
            limit=50,
        )

    def test_router_exposes_permission_management_routes(self) -> None:
        routes = {
            (route.path, tuple(sorted(route.methods or set())))
            for route in router.routes
        }

        self.assertIn(("/permissions", ("GET",)), routes)
        self.assertIn(("/permissions", ("POST",)), routes)
