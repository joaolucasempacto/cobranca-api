from datetime import datetime, timezone
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock
from uuid import uuid4

from app.routers.users import list_users, router
from app.services.user_service import UserService


class UserListingTests(TestCase):
    def test_service_delegates_pagination_to_repository(self) -> None:
        uow = Mock()
        expected = [Mock(), Mock()]
        uow.users.list.return_value = expected

        result = UserService(uow).list_users(offset=10, limit=25)

        self.assertEqual(result, expected)
        uow.users.list.assert_called_once_with(offset=10, limit=25)

    def test_router_returns_safe_paginated_users(self) -> None:
        now = datetime.now(timezone.utc)
        users = [
            SimpleNamespace(
                id=uuid4(),
                email="one@example.com",
                password_hash="hidden",
                is_active=True,
                created_at=now,
                updated_at=now,
            ),
            SimpleNamespace(
                id=uuid4(),
                email="two@example.com",
                password_hash="hidden",
                is_active=False,
                created_at=now,
                updated_at=now,
            ),
        ]
        service = Mock()
        service.list_users.return_value = users

        response = list_users(service, Mock(), offset=5, limit=20)

        self.assertEqual(len(response), 2)
        self.assertEqual(response[0].email, "one@example.com")
        self.assertNotIn("password_hash", response[0].model_dump())
        service.list_users.assert_called_once_with(offset=5, limit=20)

    def test_router_exposes_user_listing(self) -> None:
        routes = {
            (route.path, tuple(sorted(route.methods or set())))
            for route in router.routes
        }

        self.assertIn(("/users", ("GET",)), routes)
