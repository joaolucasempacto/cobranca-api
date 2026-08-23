from unittest import TestCase
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.database.session import SessionLocal
from app.main import app
from app.models.associations import user_roles
from app.models.user import User
from app.repositories.unit_of_work import UnitOfWork
from app.services.bootstrap_service import BootstrapService


class AdministrativeUserHTTPIntegrationTests(TestCase):
    def setUp(self) -> None:
        self.session = SessionLocal()
        self.admin_email = f"admin-http-{uuid4()}@example.com"
        self.user_email = f"managed-http-{uuid4()}@example.com"
        self.updated_email = f"updated-http-{uuid4()}@example.com"
        self.password = "integration-secret"
        self.admin_id: UUID | None = None
        self.user_id: UUID | None = None

        admin = BootstrapService(
            UnitOfWork(self.session)
        ).bootstrap_admin(
            self.admin_email,
            self.password,
        )
        self.admin_id = admin.id

    def tearDown(self) -> None:
        self.session.rollback()

        user_ids = [
            user_id
            for user_id in (self.user_id, self.admin_id)
            if user_id is not None
        ]
        if user_ids:
            self.session.execute(
                delete(user_roles).where(
                    user_roles.c.user_id.in_(user_ids)
                )
            )
            self.session.execute(
                delete(User).where(User.id.in_(user_ids))
            )

        self.session.commit()
        self.session.close()

    def test_admin_user_crud_flow(self) -> None:
        with TestClient(app) as client:
            login_response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": self.admin_email,
                    "password": self.password,
                },
            )
            self.assertEqual(login_response.status_code, 200)
            access_token = login_response.json()["access_token"]
            headers = {
                "Authorization": f"Bearer {access_token}",
            }

            create_response = client.post(
                "/api/v1/users",
                headers=headers,
                json={
                    "email": self.user_email,
                    "password": "managed-secret",
                    "is_active": True,
                },
            )
            self.assertEqual(create_response.status_code, 201)
            created = create_response.json()
            self.user_id = UUID(created["id"])
            self.assertEqual(created["email"], self.user_email)
            self.assertTrue(created["is_active"])
            self.assertNotIn("password_hash", created)

            detail_response = client.get(
                f"/api/v1/users/{self.user_id}",
                headers=headers,
            )
            self.assertEqual(detail_response.status_code, 200)
            self.assertEqual(
                detail_response.json()["email"],
                self.user_email,
            )

            update_response = client.patch(
                f"/api/v1/users/{self.user_id}",
                headers=headers,
                json={
                    "email": self.updated_email,
                    "is_active": False,
                },
            )
            self.assertEqual(update_response.status_code, 200)
            updated = update_response.json()
            self.assertEqual(updated["email"], self.updated_email)
            self.assertFalse(updated["is_active"])

            delete_response = client.delete(
                f"/api/v1/users/{self.user_id}",
                headers=headers,
            )
            self.assertEqual(delete_response.status_code, 204)

            missing_response = client.get(
                f"/api/v1/users/{self.user_id}",
                headers=headers,
            )
            self.assertEqual(missing_response.status_code, 404)
