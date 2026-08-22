from unittest import TestCase
from unittest.mock import Mock, patch
from uuid import uuid4

from fastapi.security import HTTPAuthorizationCredentials

from app.dependencies import (
    get_authorization_service,
    get_current_user,
    require_permission,
)
from app.exceptions.base import UnauthorizedError
from app.services.auth_service import AuthService


class AccessTokenAuthenticationTests(TestCase):
    def setUp(self) -> None:
        self.uow = Mock()
        self.service = AuthService(
            uow=self.uow,
            secret_key="test-secret",
            algorithm="HS256",
        )

    @patch("app.services.auth_service.decode_token")
    def test_authenticate_access_token_returns_active_user(
        self,
        decode_token: Mock,
    ) -> None:
        user_id = uuid4()
        user = Mock(id=user_id)
        decode_token.return_value = {
            "sub": str(user_id),
            "jti": "active-jti",
        }
        self.uow.revoked_tokens.exists_by_jti.return_value = False
        self.uow.users.get_active_by_id.return_value = user

        result = self.service.authenticate_access_token("access-token")

        self.assertIs(result, user)
        decode_token.assert_called_once_with(
            token="access-token",
            secret_key="test-secret",
            algorithm="HS256",
            expected_type="access",
        )

    @patch("app.services.auth_service.decode_token")
    def test_authenticate_access_token_rejects_revoked_token(
        self,
        decode_token: Mock,
    ) -> None:
        decode_token.return_value = {
            "sub": str(uuid4()),
            "jti": "revoked-jti",
        }
        self.uow.revoked_tokens.exists_by_jti.return_value = True

        with self.assertRaisesRegex(UnauthorizedError, "Token revogado"):
            self.service.authenticate_access_token("access-token")

        self.uow.users.get_active_by_id.assert_not_called()


class AuthenticationDependencyTests(TestCase):
    def test_get_current_user_requires_bearer_credentials(self) -> None:
        with self.assertRaisesRegex(
            UnauthorizedError,
            "Token de acesso ausente",
        ):
            get_current_user(None, Mock())

    def test_get_current_user_delegates_to_auth_service(self) -> None:
        user = Mock()
        auth_service = Mock()
        auth_service.authenticate_access_token.return_value = user
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="access-token",
        )

        result = get_current_user(credentials, auth_service)

        self.assertIs(result, user)
        auth_service.authenticate_access_token.assert_called_once_with(
            "access-token"
        )

    def test_permission_dependency_authorizes_current_user(self) -> None:
        user = Mock(id=uuid4())
        authorization_service = Mock()
        dependency = require_permission("users:write")

        result = dependency(user, authorization_service)

        self.assertIs(result, user)
        authorization_service.require_permission.assert_called_once_with(
            user.id,
            "users:write",
        )

    def test_get_authorization_service_uses_unit_of_work(self) -> None:
        uow = Mock()

        service = get_authorization_service(uow)

        self.assertIs(service._uow, uow)
