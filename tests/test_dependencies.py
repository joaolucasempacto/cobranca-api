import os
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

os.environ.setdefault("POSTGRES_USER", "postgres")
os.environ.setdefault("POSTGRES_PASSWORD", "postgres")
os.environ.setdefault("POSTGRES_DB", "cobranca")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/cobranca",
)
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")

from app.dependencies import (  # noqa: E402
    get_auth_service,
    get_db_session,
    get_unit_of_work,
)
from app.services.auth_service import AuthService  # noqa: E402


class DependencyTests(TestCase):
    @patch("app.dependencies.SessionLocal")
    def test_get_db_session_closes_session(self, session_local: Mock) -> None:
        session = Mock()
        session_local.return_value = session
        dependency = get_db_session()

        self.assertIs(next(dependency), session)
        dependency.close()

        session.close.assert_called_once_with()

    def test_get_unit_of_work_uses_same_session(self) -> None:
        session = Mock()

        uow = get_unit_of_work(session)

        self.assertIs(uow._session, session)

    @patch("app.dependencies.AuthService")
    def test_get_auth_service_uses_application_settings(
        self,
        auth_service_class: Mock,
    ) -> None:
        uow = Mock()
        expected_service = Mock(spec=AuthService)
        auth_service_class.return_value = expected_service
        settings = SimpleNamespace(
            JWT_SECRET_KEY="secret",
            JWT_ALGORITHM="HS256",
            JWT_ACCESS_TOKEN_EXPIRE_MINUTES=20,
            JWT_REFRESH_TOKEN_EXPIRE_DAYS=10,
        )

        result = get_auth_service(uow, settings)

        self.assertIs(result, expected_service)
        auth_service_class.assert_called_once_with(
            uow=uow,
            secret_key="secret",
            algorithm="HS256",
            access_token_expire_minutes=20,
            refresh_token_expire_days=10,
        )
