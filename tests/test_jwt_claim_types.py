from datetime import datetime, timedelta, timezone
from unittest import TestCase

import jwt

from app.core.jwt import decode_token
from app.exceptions.base import UnauthorizedError


class JWTClaimTypeTests(TestCase):
    def setUp(self) -> None:
        self.secret = "test-secret-key-that-is-at-least-32-bytes"
        self.now = datetime.now(timezone.utc)

    def _encode(self, *, issued_at: object, expires_at: object) -> str:
        return jwt.encode(
            {
                "sub": "user-id",
                "type": "access",
                "jti": "token-jti",
                "iat": issued_at,
                "exp": expires_at,
            },
            self.secret,
            algorithm="HS256",
        )

    def test_rejects_string_expiration_claim(self) -> None:
        token = self._encode(
            issued_at=int(self.now.timestamp()),
            expires_at=str(
                int((self.now + timedelta(hours=1)).timestamp())
            ),
        )

        with self.assertRaisesRegex(
            UnauthorizedError,
            "Token inválido ou expirado",
        ):
            decode_token(token, self.secret)

    def test_rejects_string_issued_at_claim(self) -> None:
        token = self._encode(
            issued_at=str(int(self.now.timestamp())),
            expires_at=int(
                (self.now + timedelta(hours=1)).timestamp()
            ),
        )

        with self.assertRaisesRegex(
            UnauthorizedError,
            "Token inválido ou expirado",
        ):
            decode_token(token, self.secret)
