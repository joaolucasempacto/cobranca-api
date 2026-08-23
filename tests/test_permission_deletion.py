from unittest import TestCase
from unittest.mock import Mock
from uuid import uuid4

from app.models.permission import Permission
from app.routers.permissions import delete_permission, router
from app.services.permission_service import PermissionService


class PermissionDeletionTests(TestCase):
    def test_model_soft_delete_marks_deleted(self) -> None:
        permission = Permission(
            code="users:read",
            description="Ler usuários",
        )

        permission.soft_delete()

        self.assertIsNotNone(permission.deleted_at)
        self.assertIsNotNone(permission.deleted_at.tzinfo)

    def test_service_soft_deletes_permission_and_commits(self) -> None:
        permission_id = uuid4()
        permission = Mock()
        uow = Mock()
        uow.permissions.get_by_id.return_value = permission

        PermissionService(uow).delete(permission_id)

        permission.soft_delete.assert_called_once_with()
        uow.commit.assert_called_once_with()

    def test_router_delegates_delete_to_service(self) -> None:
        permission_id = uuid4()
        service = Mock()

        response = delete_permission(permission_id, service, Mock())

        self.assertEqual(response.status_code, 204)
        service.delete.assert_called_once_with(permission_id)

    def test_router_exposes_no_content_delete(self) -> None:
        matching = [
            route
            for route in router.routes
            if route.path == "/permissions/{permission_id}"
            and "DELETE" in (route.methods or set())
        ]

        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0].status_code, 204)
