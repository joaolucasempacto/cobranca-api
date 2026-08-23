from unittest import TestCase
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.database.session import SessionLocal
from app.main import app
from app.models.associations import role_permissions, user_roles
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User
from app.repositories.unit_of_work import UnitOfWork
from app.services.bootstrap_service import (
    ADMIN_PERMISSIONS,
    ADMIN_ROLE_NAME,
    BootstrapService,
)


class AdministrativeRBACHTTPIntegrationTests(TestCase):
    def setUp(self) -> None:
        self.session = SessionLocal()
        self.admin_email = f"admin-rbac-http-{uuid4()}@example.com"
        self.password = "integration-secret"
        self.role_name = f"role-{uuid4()}"
        self.permission_code = f"feature:{uuid4()}"
        self.admin_id: UUID | None = None
        self.role_id: UUID | None = None
        self.permission_id: UUID | None = None

        self.existing_admin_role_id = self.session.scalar(
            select(Role.id).where(Role.name == ADMIN_ROLE_NAME)
        )
        self.existing_admin_permission_ids = {
            code: self.session.scalar(
                select(Permission.id).where(Permission.code == code)
            )
            for code, _ in ADMIN_PERMISSIONS
        }

        admin = BootstrapService(
            UnitOfWork(self.session)
        ).bootstrap_admin(
            self.admin_email,
            self.password,
        )
        self.admin_id = admin.id

    def tearDown(self) -> None:
        self.session.rollback()

        if self.admin_id is not None:
            self.session.execute(
                delete(user_roles).where(
                    user_roles.c.user_id == self.admin_id
                )
            )
            self.session.execute(
                delete(User).where(User.id == self.admin_id)
            )

        if self.role_id is not None:
            self.session.execute(
                delete(role_permissions).where(
                    role_permissions.c.role_id == self.role_id
                )
            )
            self.session.execute(
                delete(Role).where(Role.id == self.role_id)
            )

        if self.permission_id is not None:
            self.session.execute(
                delete(role_permissions).where(
                    role_permissions.c.permission_id == self.permission_id
                )
            )
            self.session.execute(
                delete(Permission).where(
                    Permission.id == self.permission_id
                )
            )

        admin_role = self.session.scalar(
            select(Role).where(Role.name == ADMIN_ROLE_NAME)
        )
        if (
            self.existing_admin_role_id is None
            and admin_role is not None
        ):
            self.session.execute(
                delete(role_permissions).where(
                    role_permissions.c.role_id == admin_role.id
                )
            )
            self.session.delete(admin_role)

        for code, _ in ADMIN_PERMISSIONS:
            if self.existing_admin_permission_ids[code] is not None:
                continue
            permission = self.session.scalar(
                select(Permission).where(Permission.code == code)
            )
            if permission is not None:
                self.session.execute(
                    delete(role_permissions).where(
                        role_permissions.c.permission_id == permission.id
                    )
                )
                self.session.delete(permission)

        self.session.commit()
        self.session.close()

    def test_role_permission_management_flow(self) -> None:
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

            permission_response = client.post(
                "/api/v1/permissions",
                headers=headers,
                json={
                    "code": self.permission_code,
                    "description": "Permissão de integração",
                },
            )
            self.assertEqual(permission_response.status_code, 201)
            self.permission_id = UUID(
                permission_response.json()["id"]
            )

            role_response = client.post(
                "/api/v1/roles",
                headers=headers,
                json={
                    "name": self.role_name,
                    "description": "Role de integração",
                },
            )
            self.assertEqual(role_response.status_code, 201)
            self.role_id = UUID(role_response.json()["id"])

            grant_response = client.put(
                (
                    f"/api/v1/roles/{self.role_id}/permissions/"
                    f"{self.permission_id}"
                ),
                headers=headers,
            )
            self.assertEqual(grant_response.status_code, 204)

            list_response = client.get(
                f"/api/v1/roles/{self.role_id}/permissions",
                headers=headers,
            )
            self.assertEqual(list_response.status_code, 200)
            permission_codes = {
                item["code"] for item in list_response.json()
            }
            self.assertIn(self.permission_code, permission_codes)

            revoke_response = client.delete(
                (
                    f"/api/v1/roles/{self.role_id}/permissions/"
                    f"{self.permission_id}"
                ),
                headers=headers,
            )
            self.assertEqual(revoke_response.status_code, 204)

            empty_response = client.get(
                f"/api/v1/roles/{self.role_id}/permissions",
                headers=headers,
            )
            self.assertEqual(empty_response.status_code, 200)
            self.assertEqual(empty_response.json(), [])
