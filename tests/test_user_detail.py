from datetime import datetime, timezone
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock
from uuid import uuid4

from app.routers.users import get_user_by_id, router


class UserDetailTests(TestCase):
    def test_router_delegates_user_lookup_to_service(self) -> None:
        now = datetime.now(timezone.utc)
        user_id = uuid4()
        user = SimpleNamespace(
            id=user_id,
            email="user@example.com",
            password_hash="hidden",
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        service = Mock()
        service.get_by_id.return_value = user

        response = get_user_by_id(user_id, service, Mock())

        self.assertEqual(response.id, user_id)
        self.assertEqual(response.email, "user@example.com")
        self.assertNotIn("password_hash", response.model_dump())
        service.get_by_id.assert_called_once_with(user_id)

    def test_router_exposes_user_detail_route(self) -> None:
        routes = {
            (route.path, tuple(sorted(route.methods or set())))
            for route in router.routes
        }

        self.assertIn(("/users/{user_id}", ("GET",)), routes)
