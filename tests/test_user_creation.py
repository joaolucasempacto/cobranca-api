from datetime import datetime, timezone
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch
from uuid import uuid4

from pydantic import ValidationError

from app.exceptions.base import ConflictError
from app.routers.users import create_user, router
from app.schemas.user import UserCreate, UserUpdate
from app.services.user_service import UserService


class UserCreationServiceTests(TestCase):
    @patch("app.services.user_service.hash_password")
    def test_create_hashes_password_and_commits(
        self,
        hash_password: Mock,
    ) -> None:
        uow = Mock()
        uow.users.exists_by_email.return_value = False
        hash_password.return_value = "hashed-password"
        created_user = Mock()
        uow.users.add.return_value = created_user
        service = UserService(uow)

        result = service.create(
            email="admin@example.com",
            password="secret",
            is_active=True,
        )

        self.assertIs(result, created_user)
        hash_password.assert_called_once_with("secret")
        added_user = uow.users.add.call_args.args[0]
        self.assertEqual(added_user.email, "admin@example.com")
        self.assertEqual(added_user.password_hash, "hashed-password")
        self.assertTrue(added_user.is_active)
        uow.commit.assert_called_once_with()

    def test_create_rejects_duplicate_email(self) -> None:
        uow = Mock()
        uow.users.exists_by_email.return_value = True
        service = UserService(uow)

        with self.assertRaisesRegex(ConflictError, "E-mail já cadastrado"):
            service.create("admin@example.com", "secret")

        uow.users.add.assert_not_called()
        uow.commit.assert_not_called()


class UserPasswordSchemaTests(TestCase):
    def test_create_rejects_short_password(self) -> None:
        with self.assertRaises(ValidationError):
            UserCreate(
                email="admin@example.com",
                password="short",
            )

    def test_update_rejects_short_password(self) -> None:
        with self.assertRaises(ValidationError):
            UserUpdate(password="short")


class UserCreationRouterTests(TestCase):
    def test_create_user_delegates_to_service(self) -> None:
        now = datetime.now(timezone.utc)
        created_user = SimpleNamespace(
            id=uuid4(),
            email="admin@example.com",
            password_hash="hashed-password",
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        service = Mock()
        service.create.return_value = created_user
        payload = UserCreate(
            email="admin@example.com",
            password="secret123",
        )

        response = create_user(payload, service, Mock())

        self.assertEqual(response.email, "admin@example.com")
        self.assertNotIn("password_hash", response.model_dump())
        service.create.assert_called_once_with(
            email="admin@example.com",
            password="secret123",
            is_active=True,
        )

    def test_router_exposes_user_creation_endpoint(self) -> None:
        routes = {
            (route.path, tuple(sorted(route.methods or set())), route.status_code)
            for route in router.routes
        }

        self.assertIn(("/users", ("POST",), 201), routes)
