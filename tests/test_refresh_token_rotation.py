from datetime import datetime, timezone
from unittest import TestCase
from unittest.mock import Mock, patch
from uuid import uuid4

from app.models.enums import TokenType
from app.services.auth_service import AuthService, TokenPair


class RefreshTokenRotationTests(TestCase):
    def setUp(self) -> None:
        self.uow = Mock()
        self.service = AuthService(
            uow=self.uow,
            secret_key="test-secret",
            algorithm="HS256",
            access_token_expire_minutes=20,
            refresh_token_expire_days=10,
        )

    @patch(
        "app.services.auth_service.create_refresh_token",
        return_value="new-refresh-token",
    )
    @patch(
        "app.services.auth_service.create_access_token",
        return_value="new-access-token",
    )
    @patch("app.services.auth_service.decode_token")
    def test_refresh_revokes_used_token_before_returning_new_pair(
        self,
        decode_token: Mock,
        create_access_token: Mock,
        create_refresh_token: Mock,
    ) -> None:
        user_id = uuid4()
        expires_at = 1_800_000_000
        user = Mock(id=user_id)
        decode_token.return_value = {
            "sub": str(user_id),
            "jti": "used-refresh-jti",
            "exp": expires_at,
        }
        self.uow.revoked_tokens.exists_by_jti.return_value = False
        self.uow.users.get_active_by_id.return_value = user

        result = self.service.refresh("used-refresh-token")

        self.assertEqual(
            result,
            TokenPair(
                access_token="new-access-token",
                refresh_token="new-refresh-token",
            ),
        )
        revoked_token = self.uow.revoked_tokens.add.call_args.args[0]
        self.assertEqual(revoked_token.jti, "used-refresh-jti")
        self.assertEqual(revoked_token.user_id, user_id)
        self.assertEqual(revoked_token.token_type, TokenType.REFRESH)
        self.assertEqual(
            revoked_token.expires_at,
            datetime.fromtimestamp(expires_at, tz=timezone.utc),
        )
        self.uow.commit.assert_called_once_with()
