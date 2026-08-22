from unittest import TestCase
from unittest.mock import Mock
from uuid import uuid4

from app.exceptions.base import NotFoundError
from app.services.permission_service import PermissionService
from app.services.revoked_token_service import RevokedTokenService
from app.services.role_service import RoleService
from app.services.user_service import UserService


class UserServiceTests(TestCase):
    def test_get_by_id_raises_when_missing(self) -> None:
        uow = Mock()
        uow.users.get_by_id.return_value = None

        with self.assertRaises(NotFoundError):
            UserService(uow).get_by_id(uuid4())

    def test_existence_queries_delegate_to_repository(self) -> None:
        uow = Mock()
        uow.users.exists_by_email.return_value = True
        uow.users.active_exists_by_email.return_value = False
        service = UserService(uow)

        self.assertTrue(service.email_exists("user@example.com"))
        self.assertFalse(service.active_email_exists("user@example.com"))

    def test_add_commits(self) -> None:
        uow = Mock()
        user = Mock()
        uow.users.add.return_value = user

        result = UserService(uow).add(user)

        self.assertIs(result, user)
        uow.users.add.assert_called_once_with(user)
        uow.commit.assert_called_once_with()


class RoleServiceTests(TestCase):
    def test_get_by_name_raises_when_missing(self) -> None:
        uow = Mock()
        uow.roles.get_by_name.return_value = None

        with self.assertRaises(NotFoundError):
            RoleService(uow).get_by_name("admin")

    def test_role_exists_delegates_to_repository(self) -> None:
        uow = Mock()
        uow.roles.exists_by_name.return_value = True

        self.assertTrue(RoleService(uow).role_exists("admin"))
        uow.roles.exists_by_name.assert_called_once_with("admin")

    def test_add_commits(self) -> None:
        uow = Mock()
        role = Mock()
        uow.roles.add.return_value = role

        result = RoleService(uow).add(role)

        self.assertIs(result, role)
        uow.commit.assert_called_once_with()


class PermissionServiceTests(TestCase):
    def test_get_by_code_raises_when_missing(self) -> None:
        uow = Mock()
        uow.permissions.get_by_code.return_value = None

        with self.assertRaises(NotFoundError):
            PermissionService(uow).get_by_code("users:read")

    def test_permission_exists_delegates_to_repository(self) -> None:
        uow = Mock()
        uow.permissions.exists_by_code.return_value = True

        self.assertTrue(
            PermissionService(uow).permission_exists("users:read")
        )
        uow.permissions.exists_by_code.assert_called_once_with("users:read")

    def test_add_commits(self) -> None:
        uow = Mock()
        permission = Mock()
        uow.permissions.add.return_value = permission

        result = PermissionService(uow).add(permission)

        self.assertIs(result, permission)
        uow.commit.assert_called_once_with()


class RevokedTokenServiceTests(TestCase):
    def test_get_by_jti_raises_when_missing(self) -> None:
        uow = Mock()
        uow.revoked_tokens.get_by_jti.return_value = None

        with self.assertRaises(NotFoundError):
            RevokedTokenService(uow).get_by_jti("token-jti")

    def test_is_revoked_delegates_to_repository(self) -> None:
        uow = Mock()
        uow.revoked_tokens.exists_by_jti.return_value = True

        self.assertTrue(RevokedTokenService(uow).is_revoked("token-jti"))
        uow.revoked_tokens.exists_by_jti.assert_called_once_with("token-jti")

    def test_add_commits(self) -> None:
        uow = Mock()
        token = Mock()
        uow.revoked_tokens.add.return_value = token

        result = RevokedTokenService(uow).add(token)

        self.assertIs(result, token)
        uow.commit.assert_called_once_with()
