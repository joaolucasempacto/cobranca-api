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


class APIContractTests(TestCase):
    def test_expected_api_routes_and_methods_are_registered(self) -> None:
        registered_routes = {
            (method.upper(), path)
            for path, operations in app.openapi()["paths"].items()
            if path.startswith("/api/v1/")
            for method in operations
            if method.lower()
            in {"get", "post", "put", "patch", "delete"}
        }

        self.assertEqual(registered_routes, EXPECTED_API_ROUTES)
