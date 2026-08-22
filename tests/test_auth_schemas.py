from unittest import TestCase

from pydantic import ValidationError

from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    TokenResponse,
)


class AuthSchemaTests(TestCase):
    def test_login_request_accepts_valid_credentials(self) -> None:
        payload = LoginRequest(email="user@example.com", password="secret")
        self.assertEqual(payload.email, "user@example.com")
        self.assertEqual(payload.password, "secret")

    def test_login_request_rejects_extra_fields(self) -> None:
        with self.assertRaises(ValidationError):
            LoginRequest(
                email="user@example.com",
                password="secret",
                role="admin",
            )

    def test_refresh_and_logout_require_non_empty_tokens(self) -> None:
        with self.assertRaises(ValidationError):
            RefreshRequest(refresh_token="")
        with self.assertRaises(ValidationError):
            LogoutRequest(token="")

    def test_token_response_defaults_to_bearer(self) -> None:
        payload = TokenResponse(
            access_token="access",
            refresh_token="refresh",
        )
        self.assertEqual(payload.token_type, "bearer")
