import json
from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase

from app.exceptions.base import (
    AppError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
)
from app.exceptions.handlers import (
    app_error_handler,
    unhandled_exception_handler,
)


class ExceptionHandlerTests(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.request = SimpleNamespace(
            url=SimpleNamespace(path="/api/v1/test"),
        )

    async def test_domain_errors_map_to_expected_http_statuses(self) -> None:
        cases = (
            (NotFoundError("missing"), 404),
            (ConflictError("duplicate"), 409),
            (UnauthorizedError("invalid token"), 401),
            (ForbiddenError("denied"), 403),
            (AppError("bad request"), 400),
        )

        for error, expected_status in cases:
            with self.subTest(error=type(error).__name__):
                response = await app_error_handler(self.request, error)
                self.assertEqual(response.status_code, expected_status)
                self.assertEqual(
                    json.loads(response.body),
                    {"detail": error.message},
                )

    async def test_unhandled_errors_hide_internal_details(self) -> None:
        response = await unhandled_exception_handler(
            self.request,
            RuntimeError("database password leaked"),
        )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            json.loads(response.body),
            {"detail": "Erro interno do servidor"},
        )
        self.assertNotIn(b"password", response.body)
