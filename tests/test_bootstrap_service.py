from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch
from uuid import uuid4

from app.exceptions.base import ConflictError
from app.services.bootstrap_service import ADMIN_PERMISSIONS, BootstrapService


class BootstrapServiceTests(TestCase):
    @patch("app.services.bootstrap_service.hash_password")
    def test_bootstrap_creates_admin_rbac_atomically(
        self,
        hash_password: Mock,
    ) -> None:
        uow = Mock()
        uow.permissions.get_by_code.return_value = None
        uow.permissions.exists_by_code.return_value = False
        uow.permissions.add.side_effect = lambda permission: (
            setattr(permission, "id", uuid4()) or permission
        )
        uow.roles.get_by_name.return_value = None
        uow.roles.exists_by_name.return_value = False
        role = SimpleNamespace(id=uuid4(), name="admin")
        uow.roles.add.return_value = role
        uow.roles.has_permission.return_value = False
        uow.users.get_by_email.return_value = None
        uow.users.exists_by_email.return_value = False
        user = SimpleNamespace(
            id=uuid4(),
            email="admin@example.com",
            is_active=True,
        )
        uow.users.add.return_value = user
        uow.users.has_role.return_value = False
        hash_password.return_value = "hashed-password"

        result = BootstrapService(uow).bootstrap_admin(
            "admin@example.com",
            "secret",
        )

        self.assertIs(result, user)
        self.assertEqual(
            uow.permissions.add.call_count,
            len(ADMIN_PERMISSIONS),
        )
        self.assertEqual(
            uow.roles.add_permission.call_count,
            len(ADMIN_PERMISSIONS),
        )
        uow.users.add_role.assert_called_once_with(user.id, role.id)
        uow.commit.assert_called_once_with()

    def test_bootstrap_is_idempotent_for_existing_admin(self) -> None:
        uow = Mock()
        uow.permissions.get_by_code.side_effect = [
            SimpleNamespace(id=uuid4(), code=code)
            for code, _ in ADMIN_PERMISSIONS
        ]
        role = SimpleNamespace(id=uuid4(), name="admin")
        user = SimpleNamespace(
            id=uuid4(),
            email="admin@example.com",
            is_active=True,
        )
        uow.roles.get_by_name.return_value = role
        uow.roles.has_permission.return_value = True
        uow.users.get_by_email.return_value = user
        uow.users.has_role.return_value = True

        result = BootstrapService(uow).bootstrap_admin(
            user.email,
            "ignored",
        )

        self.assertIs(result, user)
        uow.permissions.add.assert_not_called()
        uow.roles.add.assert_not_called()
        uow.roles.add_permission.assert_not_called()
        uow.users.add.assert_not_called()
        uow.users.add_role.assert_not_called()
        uow.commit.assert_called_once_with()

    def test_bootstrap_rejects_soft_deleted_admin_role(self) -> None:
        uow = Mock()
        uow.permissions.get_by_code.side_effect = [
            SimpleNamespace(id=uuid4(), code=code)
            for code, _ in ADMIN_PERMISSIONS
        ]
        uow.roles.get_by_name.return_value = None
        uow.roles.exists_by_name.return_value = True

        with self.assertRaisesRegex(
            ConflictError,
            "removido logicamente",
        ):
            BootstrapService(uow).bootstrap_admin(
                "admin@example.com",
                "secret",
            )

        uow.commit.assert_not_called()
