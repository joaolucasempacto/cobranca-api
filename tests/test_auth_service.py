from datetime import datetime, timezone
from unittest import TestCase
from unittest.mock import Mock, patch
from uuid import uuid4

from app.exceptions.base import UnauthorizedError
from app.models.enums import TokenType
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

    @patch("app.services.auth_service.decode_token")
    def test_refresh_rejects_revoked_token(self, decode_token: Mock) -> None:
        user_id = uuid4()
        decode_token.return_value = {
            "sub": str(user_id),
            "jti": "revoked-jti",
        }
        self.uow.revoked_tokens.exists_by_jti.return_value = True

        with self.assertRaisesRegex(UnauthorizedError, "Token revogado"):
            self.service.refresh("refresh-token")

        self.uow.revoked_tokens.exists_by_jti.assert_called_once_with(
            "revoked-jti"
        )
        self.uow.users.get_active_by_id.assert_not_called()

    @patch("app.services.auth_service.decode_token")
    def test_refresh_rejects_inactive_user(self, decode_token: Mock) -> None:
        user_id = uuid4()
        decode_token.return_value = {
            "sub": str(user_id),
            "jti": "active-jti",
        }
        self.uow.revoked_tokens.exists_by_jti.return_value = False
        self.uow.users.get_active_by_id.return_value = None

        with self.assertRaisesRegex(
            UnauthorizedError,
            "Usuário inativo ou não encontrado",
        ):
            self.service.refresh("refresh-token")

        self.uow.users.get_active_by_id.assert_called_once_with(user_id)

    @patch(
        "app.services.auth_service.create_refresh_token",
        return_value="new-refresh-token",
    )
    @patch(
        "app.services.auth_service.create_access_token",
        return_value="new-access-token",
    )
    @patch("app.services.auth_service.decode_token")
    def test_refresh_returns_new_token_pair(
        self,
        decode_token: Mock,
        create_access_token: Mock,
        create_refresh_token: Mock,
    ) -> None:
        user_id = uuid4()
        user = Mock(id=user_id)
        decode_token.return_value = {
            "sub": str(user_id),
            "jti": "active-jti",
        }
        self.uow.revoked_tokens.exists_by_jti.return_value = False
        self.uow.users.get_active_by_id.return_value = user

        result = self.service.refresh("refresh-token")

        self.assertEqual(
            result,
            TokenPair(
                access_token="new-access-token",
                refresh_token="new-refresh-token",
            ),
        )
        decode_token.assert_called_once_with(
            token="refresh-token",
            secret_key="test-secret",
            algorithm="HS256",
            expected_type="refresh",
        )
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

    @patch("app.services.auth_service.decode_token")
    def test_logout_revokes_token_and_commits(self, decode_token: Mock) -> None:
        user_id = uuid4()
        expires_at = 1_800_000_000
        decode_token.return_value = {
            "sub": str(user_id),
            "jti": "logout-jti",
            "type": "refresh",
            "exp": expires_at,
        }
        self.uow.revoked_tokens.exists_by_jti.return_value = False

        self.service.logout("refresh-token")

        decode_token.assert_called_once_with(
            token="refresh-token",
            secret_key="test-secret",
            algorithm="HS256",
        )
        revoked_token = self.uow.revoked_tokens.add.call_args.args[0]
        self.assertEqual(revoked_token.jti, "logout-jti")
        self.assertEqual(revoked_token.user_id, user_id)
        self.assertEqual(revoked_token.token_type, TokenType.REFRESH)
        self.assertEqual(
            revoked_token.expires_at,
            datetime.fromtimestamp(expires_at, tz=timezone.utc),
        )
        self.uow.commit.assert_called_once_with()

    @patch("app.services.auth_service.decode_token")
    def test_logout_is_idempotent_for_revoked_token(
        self,
        decode_token: Mock,
    ) -> None:
        decode_token.return_value = {
            "sub": str(uuid4()),
            "jti": "revoked-jti",
            "type": "refresh",
            "exp": 1_800_000_000,
        }
        self.uow.revoked_tokens.exists_by_jti.return_value = True

        self.service.logout("refresh-token")

        self.uow.revoked_tokens.add.assert_not_called()
        self.uow.commit.assert_not_called()

    @patch("app.services.auth_service.decode_token")
    def test_logout_rejects_invalid_subject(self, decode_token: Mock) -> None:
        decode_token.return_value = {
            "sub": "invalid-user-id",
            "jti": "logout-jti",
            "type": "refresh",
            "exp": 1_800_000_000,
        }
        self.uow.revoked_tokens.exists_by_jti.return_value = False

        with self.assertRaisesRegex(
            UnauthorizedError,
            "Token inválido ou expirado",
        ):
            self.service.logout("refresh-token")

        self.uow.revoked_tokens.add.assert_not_called()
        self.uow.commit.assert_not_called()
