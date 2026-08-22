from unittest import TestCase
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.core.security import hash_password
from app.database.session import SessionLocal
from app.main import app
from app.models.user import User


class AuthenticationHTTPIntegrationTests(TestCase):
    def setUp(self) -> None:
        self.email = f"http-login-{uuid4()}@example.com"
        self.password = "integration-secret"
        self.session = SessionLocal()
        self.session.add(
            User(
                email=self.email,
                password_hash=hash_password(self.password),
                is_active=True,
            )
        )
        self.session.commit()

    def tearDown(self) -> None:
        self.session.rollback()
        self.session.execute(
            delete(User).where(User.email == self.email)
        )
        self.session.commit()
        self.session.close()

    def test_login_returns_access_and_refresh_tokens(self) -> None:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": self.email,
                    "password": self.password,
                },
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["token_type"], "bearer")
        self.assertIsInstance(body["access_token"], str)
        self.assertIsInstance(body["refresh_token"], str)
        self.assertTrue(body["access_token"])
        self.assertTrue(body["refresh_token"])
        self.assertNotEqual(
            body["access_token"],
            body["refresh_token"],
        )

    def test_refresh_logout_and_revocation_flow(self) -> None:
        with TestClient(app) as client:
            login_response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": self.email,
                    "password": self.password,
                },
            )
            self.assertEqual(login_response.status_code, 200)
            initial_refresh_token = login_response.json()["refresh_token"]

            refresh_response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": initial_refresh_token},
            )
            self.assertEqual(refresh_response.status_code, 200)
            refreshed_body = refresh_response.json()
            refreshed_refresh_token = refreshed_body["refresh_token"]
            self.assertNotEqual(
                refreshed_body["access_token"],
                refreshed_refresh_token,
            )

            logout_response = client.post(
                "/api/v1/auth/logout",
                json={"token": refreshed_refresh_token},
            )
            self.assertEqual(logout_response.status_code, 204)

            revoked_refresh_response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": refreshed_refresh_token},
            )

        self.assertEqual(revoked_refresh_response.status_code, 401)
