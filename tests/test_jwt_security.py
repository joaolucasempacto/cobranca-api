from datetime import datetime, timedelta, timezone
from unittest import TestCase

import jwt

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

    def test_create_rejects_empty_subject(self) -> None:
        with self.assertRaises(ValueError):
            create_access_token("", SECRET_KEY)

        with self.assertRaises(ValueError):
            create_refresh_token("", SECRET_KEY)

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

    def test_decode_rejects_malformed_token(self) -> None:
        with self.assertRaises(UnauthorizedError):
            decode_token("not-a-jwt", SECRET_KEY)

    def test_decode_rejects_missing_required_claim(self) -> None:
        now = datetime.now(timezone.utc)
        token = jwt.encode(
            {
                "sub": "user-123",
                "type": "access",
                "iat": now,
                "exp": now + timedelta(minutes=5),
            },
            SECRET_KEY,
            algorithm="HS256",
        )

        with self.assertRaises(UnauthorizedError):
            decode_token(token, SECRET_KEY)
