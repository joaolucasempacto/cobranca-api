from unittest import TestCase
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete, insert

from app.core.security import hash_password
from app.database.session import SessionLocal
from app.main import app
from app.models.associations import role_permissions, user_roles
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User


class RBACHTTPIntegrationTests(TestCase):
    def setUp(self) -> None:
        suffix = uuid4()
        self.allowed_email = f"rbac-allowed-{suffix}@example.com"
        self.denied_email = f"rbac-denied-{suffix}@example.com"
        self.password = "integration-secret"
        self.role_name = f"rbac-reader-{suffix}"

        self.session = SessionLocal()

        self.allowed_user = User(
            email=self.allowed_email,
            password_hash=hash_password(self.password),
            is_active=True,
        )
        self.denied_user = User(
            email=self.denied_email,
            password_hash=hash_password(self.password),
            is_active=True,
        )
        self.role = Role(
            name=self.role_name,
            description="RBAC integration role",
        )
        self.permission = Permission(
            code="users:read",
            description="RBAC integration permission",
        )
        self.session.add_all(
            [
                self.allowed_user,
                self.denied_user,
                self.role,
                self.permission,
            ]
        )
        self.session.flush()

        self.session.execute(
            insert(user_roles).values(
                user_id=self.allowed_user.id,
                role_id=self.role.id,
            )
        )
        self.session.execute(
            insert(role_permissions).values(
                role_id=self.role.id,
                permission_id=self.permission.id,
            )
        )
        self.session.commit()

    def tearDown(self) -> None:
        self.session.rollback()
        self.session.execute(
            delete(user_roles).where(
                user_roles.c.user_id.in_(
                    [self.allowed_user.id, self.denied_user.id]
                )
            )
        )
        self.session.execute(
            delete(role_permissions).where(
                role_permissions.c.role_id == self.role.id
            )
        )
        self.session.execute(
            delete(User).where(
                User.id.in_(
                    [self.allowed_user.id, self.denied_user.id]
                )
            )
        )
        self.session.execute(
            delete(Role).where(Role.id == self.role.id)
        )
        self.session.execute(
            delete(Permission).where(
                Permission.id == self.permission.id
            )
        )
        self.session.commit()
        self.session.close()

    def _login(self, email: str) -> str:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": email,
                    "password": self.password,
                },
            )

        self.assertEqual(response.status_code, 200)
        return response.json()["access_token"]

    def test_user_with_permission_can_access_protected_endpoint(self) -> None:
        access_token = self._login(self.allowed_email)

        with TestClient(app) as client:
            response = client.get(
                "/api/v1/users",
                headers={"Authorization": f"Bearer {access_token}"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_user_without_permission_receives_forbidden(self) -> None:
        access_token = self._login(self.denied_email)

        with TestClient(app) as client:
            response = client.get(
                "/api/v1/users",
                headers={"Authorization": f"Bearer {access_token}"},
            )

        self.assertEqual(response.status_code, 403)
