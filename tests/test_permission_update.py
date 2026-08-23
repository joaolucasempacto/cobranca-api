from datetime import datetime, timezone
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock
from uuid import uuid4

from app.exceptions.base import ConflictError
from app.routers.permissions import router, update_permission
from app.schemas.permission import PermissionUpdate
from app.services.permission_service import PermissionService


class PermissionUpdateTests(TestCase):
    def test_update_permission_changes_fields_and_commits(self) -> None:
        uow = Mock()
        permission = Mock(code="users:read")
        uow.permissions.get_by_id.return_value = permission
        uow.permissions.exists_by_code.return_value = False
        permission_id = uuid4()

        result = PermissionService(uow).update(
            permission_id,
            code="users:list",
            description="Listar usuários",
            description_provided=True,
        )

        self.assertIs(result, permission)
        permission.update_details.assert_called_once_with(
            code="users:list",
            description="Listar usuários",
            description_provided=True,
        )
        uow.commit.assert_called_once_with()

    def test_update_permission_can_clear_description(self) -> None:
        uow = Mock()
        permission = Mock(code="users:read")
        uow.permissions.get_by_id.return_value = permission
        permission_id = uuid4()

        PermissionService(uow).update(
            permission_id,
            description=None,
            description_provided=True,
        )

        permission.update_details.assert_called_once_with(
            code=None,
            description=None,
            description_provided=True,
        )
        uow.commit.assert_called_once_with()

    def test_update_permission_rejects_duplicate_code(self) -> None:
        uow = Mock()
        permission = Mock(code="users:read")
        uow.permissions.get_by_id.return_value = permission
        uow.permissions.exists_by_code.return_value = True

        with self.assertRaisesRegex(
            ConflictError,
            "Permissão já cadastrada",
        ):
            PermissionService(uow).update(
                uuid4(),
                code="users:write",
            )

        permission.update_details.assert_not_called()
        uow.commit.assert_not_called()

    def test_update_schema_rejects_empty_payload(self) -> None:
        with self.assertRaises(ValueError):
            PermissionUpdate()

    def test_update_schema_accepts_explicit_null_description(self) -> None:
        payload = PermissionUpdate(description=None)

        self.assertIn("description", payload.model_fields_set)
        self.assertIsNone(payload.description)

    def test_update_schema_rejects_null_code_only(self) -> None:
        with self.assertRaises(ValueError):
            PermissionUpdate(code=None)

    def test_router_preserves_explicit_null_description(self) -> None:
        permission_id = uuid4()
        now = datetime.now(timezone.utc)
        permission = SimpleNamespace(
            id=permission_id,
            code="users:read",
            description=None,
            created_at=now,
            updated_at=now,
        )
        permission_service = Mock()
        permission_service.update.return_value = permission
        payload = PermissionUpdate(description=None)

        response = update_permission(
            permission_id,
            payload,
            permission_service,
            Mock(),
        )

        self.assertIsNone(response.description)
        permission_service.update.assert_called_once_with(
            permission_id=permission_id,
            code=None,
            description=None,
            description_provided=True,
        )

    def test_router_exposes_permission_update(self) -> None:
        routes = {
            (route.path, tuple(sorted(route.methods or set())))
            for route in router.routes
        }
        self.assertIn(
            ("/permissions/{permission_id}", ("PATCH",)),
            routes,
        )
