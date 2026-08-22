from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock

from app.routers.auth import login, logout, refresh, router
from app.schemas.auth import LoginRequest, LogoutRequest, RefreshRequest


class AuthRouterTests(TestCase):
    def test_login_delegates_to_auth_service(self) -> None:
        auth_service = Mock()
        auth_service.authenticate.return_value = SimpleNamespace(
            access_token="access",
            refresh_token="refresh",
        )

        response = login(
            LoginRequest(email="user@example.com", password="secret"),
            auth_service,
        )

        self.assertEqual(response.access_token, "access")
        self.assertEqual(response.refresh_token, "refresh")
        self.assertEqual(response.token_type, "bearer")
        auth_service.authenticate.assert_called_once_with(
            "user@example.com",
            "secret",
        )

    def test_refresh_delegates_to_auth_service(self) -> None:
        auth_service = Mock()
        auth_service.refresh.return_value = SimpleNamespace(
            access_token="new-access",
            refresh_token="new-refresh",
        )

        response = refresh(
            RefreshRequest(refresh_token="old-refresh"),
            auth_service,
        )

        self.assertEqual(response.access_token, "new-access")
        self.assertEqual(response.refresh_token, "new-refresh")
        auth_service.refresh.assert_called_once_with("old-refresh")

    def test_logout_delegates_to_auth_service(self) -> None:
        auth_service = Mock()

        result = logout(LogoutRequest(token="access-token"), auth_service)

        self.assertIsNone(result)
        auth_service.logout.assert_called_once_with("access-token")

    def test_router_exposes_auth_endpoints(self) -> None:
        routes = {
            (route.path, tuple(sorted(route.methods or set())))
            for route in router.routes
        }

        self.assertIn(("/auth/login", ("POST",)), routes)
        self.assertIn(("/auth/refresh", ("POST",)), routes)
        self.assertIn(("/auth/logout", ("POST",)), routes)
