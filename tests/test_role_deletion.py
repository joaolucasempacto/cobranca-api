from unittest import TestCase
from unittest.mock import Mock
from uuid import uuid4

from app.models.role import Role
from app.routers.roles import delete_role, router
from app.services.role_service import RoleService


class RoleDeletionTests(TestCase):
    def test_model_soft_delete_marks_deleted(self) -> None:
        role = Role(name="admin", description="Administradores")

        role.soft_delete()

        self.assertIsNotNone(role.deleted_at)
        self.assertIsNotNone(role.deleted_at.tzinfo)

    def test_service_soft_deletes_role_and_commits(self) -> None:
        role_id = uuid4()
        role = Mock()
        uow = Mock()
        uow.roles.get_by_id.return_value = role

        RoleService(uow).delete(role_id)

        role.soft_delete.assert_called_once_with()
        uow.commit.assert_called_once_with()

    def test_router_delegates_delete_to_service(self) -> None:
        role_id = uuid4()
        service = Mock()

        response = delete_role(role_id, service, Mock())

        self.assertEqual(response.status_code, 204)
        service.delete.assert_called_once_with(role_id)

    def test_router_exposes_no_content_delete(self) -> None:
        matching = [
            route
            for route in router.routes
            if route.path == "/roles/{role_id}"
            and "DELETE" in (route.methods or set())
        ]

        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0].status_code, 204)
