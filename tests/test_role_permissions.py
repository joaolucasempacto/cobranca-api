from unittest import TestCase
from unittest.mock import Mock
from uuid import uuid4

from app.exceptions.base import ConflictError, NotFoundError
from app.routers.roles import (
    grant_role_permission,
    list_role_permissions,
    revoke_role_permission,
)
from app.services.role_service import RoleService


class RolePermissionServiceTests(TestCase):
    def test_grant_permission_validates_and_commits(self) -> None:
        role_id = uuid4()
        permission_id = uuid4()
        uow = Mock()
        uow.roles.get_by_id.return_value = Mock()
        uow.permissions.get_by_id.return_value = Mock()
        uow.roles.has_permission.return_value = False

        RoleService(uow).grant_permission(role_id, permission_id)

        uow.roles.add_permission.assert_called_once_with(
            role_id,
            permission_id,
        )
        uow.commit.assert_called_once_with()

    def test_grant_permission_rejects_duplicate(self) -> None:
        role_id = uuid4()
        permission_id = uuid4()
        uow = Mock()
        uow.roles.get_by_id.return_value = Mock()
        uow.permissions.get_by_id.return_value = Mock()
        uow.roles.has_permission.return_value = True

        with self.assertRaises(ConflictError):
            RoleService(uow).grant_permission(role_id, permission_id)

        uow.roles.add_permission.assert_not_called()
        uow.commit.assert_not_called()

    def test_revoke_permission_requires_existing_assignment(self) -> None:
        role_id = uuid4()
        permission_id = uuid4()
        uow = Mock()
        uow.roles.get_by_id.return_value = Mock()
        uow.permissions.get_by_id.return_value = Mock()
        uow.roles.has_permission.return_value = False

        with self.assertRaises(NotFoundError):
            RoleService(uow).revoke_permission(role_id, permission_id)

        uow.roles.remove_permission.assert_not_called()
        uow.commit.assert_not_called()

    def test_list_permissions_validates_role(self) -> None:
        role_id = uuid4()
        uow = Mock()
        uow.roles.get_by_id.return_value = Mock()
        expected = [Mock(), Mock()]
        uow.roles.list_permissions.return_value = expected

        result = RoleService(uow).list_permissions(role_id)

        self.assertEqual(result, expected)
        uow.roles.list_permissions.assert_called_once_with(role_id)


class RolePermissionRouterTests(TestCase):
    def test_router_delegates_grant_and_revoke(self) -> None:
        role_id = uuid4()
        permission_id = uuid4()
        service = Mock()

        grant_response = grant_role_permission(
            role_id,
            permission_id,
            service,
            Mock(),
        )
        revoke_response = revoke_role_permission(
            role_id,
            permission_id,
            service,
            Mock(),
        )

        self.assertEqual(grant_response.status_code, 204)
        self.assertEqual(revoke_response.status_code, 204)
        service.grant_permission.assert_called_once_with(
            role_id,
            permission_id,
        )
        service.revoke_permission.assert_called_once_with(
            role_id,
            permission_id,
        )

    def test_router_delegates_permission_listing(self) -> None:
        role_id = uuid4()
        service = Mock()
        service.list_permissions.return_value = []

        result = list_role_permissions(role_id, service, Mock())

        self.assertEqual(result, [])
        service.list_permissions.assert_called_once_with(role_id)
