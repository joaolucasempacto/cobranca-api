from collections.abc import Iterable
from typing import Any
from unittest import TestCase

from app.main import app


EXPECTED_API_ROUTES = {
    ("GET", "/api/v1/health"),
    ("POST", "/api/v1/auth/login"),
    ("POST", "/api/v1/auth/refresh"),
    ("POST", "/api/v1/auth/logout"),
    ("GET", "/api/v1/users/me"),
    ("GET", "/api/v1/users"),
    ("POST", "/api/v1/users"),
    ("GET", "/api/v1/users/{user_id}"),
    ("PATCH", "/api/v1/users/{user_id}"),
    ("DELETE", "/api/v1/users/{user_id}"),
    ("GET", "/api/v1/users/{user_id}/roles"),
    ("PUT", "/api/v1/users/{user_id}/roles/{role_id}"),
    ("DELETE", "/api/v1/users/{user_id}/roles/{role_id}"),
    ("GET", "/api/v1/roles"),
    ("POST", "/api/v1/roles"),
    ("GET", "/api/v1/roles/{role_id}"),
    ("PATCH", "/api/v1/roles/{role_id}"),
    ("DELETE", "/api/v1/roles/{role_id}"),
    ("GET", "/api/v1/roles/{role_id}/permissions"),
    ("PUT", "/api/v1/roles/{role_id}/permissions/{permission_id}"),
    ("DELETE", "/api/v1/roles/{role_id}/permissions/{permission_id}"),
    ("GET", "/api/v1/permissions"),
    ("POST", "/api/v1/permissions"),
    ("GET", "/api/v1/permissions/{permission_id}"),
    ("PATCH", "/api/v1/permissions/{permission_id}"),
    ("DELETE", "/api/v1/permissions/{permission_id}"),
}


def iter_routes(routes: Iterable[Any]) -> Iterable[Any]:
    for route in routes:
        nested_routes = getattr(route, "routes", None)
        if nested_routes is not None:
            yield from iter_routes(nested_routes)
        else:
            yield route


class APIContractTests(TestCase):
    def test_expected_api_routes_and_methods_are_registered(self) -> None:
        registered_routes: set[tuple[str, str]] = set()

        for route in iter_routes(app.router.routes):
            path = getattr(route, "path", None)
            methods = getattr(route, "methods", None)
            if not isinstance(path, str) or not path.startswith("/api/v1/"):
                continue

            for method in methods or set():
                registered_routes.add((method, path))

        self.assertEqual(registered_routes, EXPECTED_API_ROUTES)
