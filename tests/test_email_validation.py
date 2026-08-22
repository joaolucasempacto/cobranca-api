from unittest import TestCase

from pydantic import ValidationError

from app.schemas.auth import LoginRequest
from app.schemas.user import UserCreate, UserUpdate


class EmailValidationTests(TestCase):
    def test_login_rejects_invalid_email(self) -> None:
        with self.assertRaises(ValidationError):
            LoginRequest(email="invalid-email", password="secret")

    def test_user_create_rejects_invalid_email(self) -> None:
        with self.assertRaises(ValidationError):
            UserCreate(email="invalid-email", password="secret")

    def test_user_update_rejects_invalid_email(self) -> None:
        with self.assertRaises(ValidationError):
            UserUpdate(email="invalid-email")

    def test_valid_email_is_accepted(self) -> None:
        payload = UserCreate(
            email="person@example.com",
            password="secret",
        )

        self.assertEqual(str(payload.email), "person@example.com")
