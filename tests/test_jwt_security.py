from unittest import TestCase

from app.core.jwt import create_access_token, create_refresh_token, decode_token
from app.exceptions.base import UnauthorizedError

SECRET_KEY = "test-secret-key-with-enough-entropy"


class JwtSecurityTests(TestCase):
    def test_access_token_contains_required_claims(self) -> None:
        token = create_access_token("user-123", SECRET_KEY)

        payload = decode_token(token, SECRET_KEY, expected_type="access")

        self.assertEqual(payload["sub"], "user-123")
        self.assertEqual(payload["type"], "access")
        self.assertIn("jti", payload)
        self.assertIn("iat", payload)
        self.assertIn("exp", payload)

    def test_refresh_token_contains_refresh_type(self) -> None:
        token = create_refresh_token("user-123", SECRET_KEY)

        payload = decode_token(token, SECRET_KEY, expected_type="refresh")

        self.assertEqual(payload["type"], "refresh")

    def test_decode_rejects_wrong_expected_type(self) -> None:
        token = create_access_token("user-123", SECRET_KEY)

        with self.assertRaises(UnauthorizedError):
            decode_token(token, SECRET_KEY, expected_type="refresh")

    def test_decode_rejects_wrong_secret(self) -> None:
        token = create_access_token("user-123", SECRET_KEY)

        with self.assertRaises(UnauthorizedError):
            decode_token(token, "different-secret")

    def test_decode_rejects_expired_token(self) -> None:
        token = create_access_token(
            "user-123",
            SECRET_KEY,
            expires_minutes=-1,
        )

        with self.assertRaises(UnauthorizedError):
            decode_token(token, SECRET_KEY)
