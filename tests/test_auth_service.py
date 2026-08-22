from unittest import TestCase
from unittest.mock import Mock, patch
from uuid import uuid4

from app.exceptions.base import UnauthorizedError
from app.services.auth_service import AuthService, TokenPair


class AuthServiceTests(TestCase):
    def setUp(self) -> None:
        self.uow = Mock()
        self.service = AuthService(
            uow=self.uow,
            secret_key="test-secret",
            algorithm="HS256",
            access_token_expire_minutes=20,
            refresh_token_expire_days=10,
        )

    def test_authenticate_rejects_missing_or_inactive_user(self) -> None:
        self.uow.users.get_active_by_email.return_value = None

        with self.assertRaisesRegex(UnauthorizedError, "Credenciais inválidas"):
            self.service.authenticate("user@example.com", "secret")

    @patch("app.services.auth_service.verify_password", return_value=False)
    def test_authenticate_rejects_invalid_password(
        self,
        verify_password: Mock,
    ) -> None:
        user = Mock(password_hash="stored-hash")
        self.uow.users.get_active_by_email.return_value = user

        with self.assertRaisesRegex(UnauthorizedError, "Credenciais inválidas"):
            self.service.authenticate("user@example.com", "wrong")

        verify_password.assert_called_once_with("wrong", "stored-hash")

    @patch(
        "app.services.auth_service.create_refresh_token",
        return_value="refresh-token",
    )
    @patch(
        "app.services.auth_service.create_access_token",
        return_value="access-token",
    )
    @patch("app.services.auth_service.verify_password", return_value=True)
    def test_authenticate_returns_access_and_refresh_tokens(
        self,
        verify_password: Mock,
        create_access_token: Mock,
        create_refresh_token: Mock,
    ) -> None:
        user_id = uuid4()
        user = Mock(id=user_id, password_hash="stored-hash")
        self.uow.users.get_active_by_email.return_value = user

        result = self.service.authenticate("user@example.com", "secret")

        self.assertEqual(
            result,
            TokenPair(
                access_token="access-token",
                refresh_token="refresh-token",
            ),
        )
        verify_password.assert_called_once_with("secret", "stored-hash")
        create_access_token.assert_called_once_with(
            subject=str(user_id),
            secret_key="test-secret",
            algorithm="HS256",
            expires_minutes=20,
        )
        create_refresh_token.assert_called_once_with(
            subject=str(user_id),
            secret_key="test-secret",
            algorithm="HS256",
            expires_days=10,
        )
