from datetime import datetime, timezone
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch
from uuid import uuid4

from pydantic import ValidationError

from app.exceptions.base import ConflictError
from app.models.user import User
from app.routers.users import update_user
from app.schemas.user import UserUpdate
from app.services.user_service import UserService


class UserUpdateTests(TestCase):
    def test_model_updates_user_details(self) -> None:
        user = User(
            email="old@example.com",
            password_hash="old-hash",
            is_active=True,
        )

        user.update_details(
            email="new@example.com",
            password_hash="new-hash",
            is_active=False,
        )

        self.assertEqual(user.email, "new@example.com")
        self.assertEqual(user.password_hash, "new-hash")
        self.assertFalse(user.is_active)

    @patch("app.services.user_service.hash_password")
    def test_service_updates_fields_and_commits(
        self,
        hash_password: Mock,
    ) -> None:
        user_id = uuid4()
        user = Mock()
        user.email = "old@example.com"
        uow = Mock()
        uow.users.get_by_id.return_value = user
        uow.users.exists_by_email.return_value = False
        hash_password.return_value = "new-hash"

        result = UserService(uow).update(
            user_id,
            email="new@example.com",
            password="secret",
            is_active=False,
        )

        self.assertIs(result, user)
        user.update_details.assert_called_once_with(
            email="new@example.com",
            password_hash="new-hash",
            is_active=False,
        )
        uow.commit.assert_called_once_with()

    def test_service_rejects_duplicate_email(self) -> None:
        user_id = uuid4()
        user = SimpleNamespace(email="old@example.com")
        uow = Mock()
        uow.users.get_by_id.return_value = user
        uow.users.exists_by_email.return_value = True

        with self.assertRaises(ConflictError):
            UserService(uow).update(
                user_id,
                email="used@example.com",
            )

        uow.commit.assert_not_called()

    def test_schema_requires_at_least_one_field(self) -> None:
        with self.assertRaises(ValidationError):
            UserUpdate()

    def test_schema_rejects_null_only_update(self) -> None:
        with self.assertRaises(ValidationError):
            UserUpdate(email=None, password=None, is_active=None)

    def test_router_delegates_to_service(self) -> None:
        user_id = uuid4()
        now = datetime.now(timezone.utc)
        user = SimpleNamespace(
            id=user_id,
            email="new@example.com",
            is_active=False,
            created_at=now,
            updated_at=now,
        )
        service = Mock()
        service.update.return_value = user

        response = update_user(
            user_id,
            UserUpdate(email="new@example.com"),
            service,
            Mock(),
        )

        self.assertEqual(response.email, "new@example.com")
        service.update.assert_called_once_with(
            user_id,
            email="new@example.com",
            password=None,
            is_active=None,
        )
