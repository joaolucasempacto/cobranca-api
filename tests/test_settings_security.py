from unittest import TestCase

from pydantic import ValidationError

from app.core.config import Settings


class SettingsSecurityTests(TestCase):
    def setUp(self) -> None:
        self.base_settings = {
            "POSTGRES_USER": "cobranca",
            "POSTGRES_PASSWORD": "cobranca",
            "POSTGRES_DB": "cobranca_test",
            "POSTGRES_HOST": "localhost",
            "POSTGRES_PORT": 5432,
            "DATABASE_URL": (
                "postgresql+psycopg://"
                "cobranca:cobranca@localhost:5432/cobranca_test"
            ),
            "JWT_SECRET_KEY": "x" * 32,
        }

    def test_rejects_short_jwt_secret(self) -> None:
        settings = self.base_settings | {"JWT_SECRET_KEY": "short-secret"}

        with self.assertRaises(ValidationError):
            Settings(**settings)

    def test_rejects_non_positive_access_token_expiration(self) -> None:
        settings = self.base_settings | {
            "JWT_ACCESS_TOKEN_EXPIRE_MINUTES": 0,
        }

        with self.assertRaises(ValidationError):
            Settings(**settings)

    def test_rejects_non_positive_refresh_token_expiration(self) -> None:
        settings = self.base_settings | {
            "JWT_REFRESH_TOKEN_EXPIRE_DAYS": 0,
        }

        with self.assertRaises(ValidationError):
            Settings(**settings)

    def test_accepts_valid_security_settings(self) -> None:
        settings = Settings(**self.base_settings)

        self.assertEqual(settings.JWT_SECRET_KEY, "x" * 32)
        self.assertEqual(settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES, 15)
        self.assertEqual(settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS, 7)
