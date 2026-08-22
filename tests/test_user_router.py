from datetime import datetime, timezone
from types import SimpleNamespace
from unittest import TestCase
from uuid import uuid4

from app.routers.users import get_me, router


class UserRouterTests(TestCase):
    def test_get_me_returns_safe_user_response(self) -> None:
        now = datetime.now(timezone.utc)
        user = SimpleNamespace(
            id=uuid4(),
            email="user@example.com",
            password_hash="secret-hash",
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        response = get_me(user)

        self.assertEqual(response.id, user.id)
        self.assertEqual(response.email, user.email)
        self.assertTrue(response.is_active)
        self.assertNotIn("password_hash", response.model_dump())

    def test_router_exposes_authenticated_profile_endpoint(self) -> None:
        routes = {
            (route.path, tuple(sorted(route.methods or set())))
            for route in router.routes
        }

        self.assertIn(("/users/me", ("GET",)), routes)
