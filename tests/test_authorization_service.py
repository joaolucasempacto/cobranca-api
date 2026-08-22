from unittest import TestCase
from unittest.mock import Mock
from uuid import uuid4

from app.exceptions.base import ForbiddenError
from app.services.authorization_service import AuthorizationService


class AuthorizationServiceTests(TestCase):
    def test_require_permission_allows_authorized_user(self) -> None:
        uow = Mock()
        user_id = uuid4()
        uow.users.has_permission.return_value = True

        AuthorizationService(uow).require_permission(user_id, "users:read")

        uow.users.has_permission.assert_called_once_with(user_id, "users:read")

    def test_require_permission_denies_unauthorized_user(self) -> None:
        uow = Mock()
        uow.users.has_permission.return_value = False

        with self.assertRaises(ForbiddenError):
            AuthorizationService(uow).require_permission(
                uuid4(),
                "users:write",
            )

    def test_require_permission_uses_requested_code(self) -> None:
        uow = Mock()
        user_id = uuid4()
        uow.users.has_permission.return_value = True
        service = AuthorizationService(uow)

        service.require_permission(user_id, "billing:read")

        uow.users.has_permission.assert_called_once_with(
            user_id,
            "billing:read",
        )
