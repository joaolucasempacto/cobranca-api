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


class AdministrativeRolePermissionCRUDHTTPIntegrationTests(TestCase):
    def setUp(self) -> None:
        self.session = SessionLocal()
        self.admin_email = f"admin-crud-http-{uuid4()}@example.com"
        self.password = "integration-secret"
        self.role_name = f"crud-role-{uuid4()}"
        self.permission_code = f"crud:{uuid4()}"
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

    def test_role_and_permission_crud_lifecycle(self) -> None:
        with TestClient(app) as client:
            login_response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": self.admin_email,
                    "password": self.password,
                },
            )
            self.assertEqual(login_response.status_code, 200)
            headers = {
                "Authorization": (
                    f"Bearer {login_response.json()['access_token']}"
                )
            }

            permission_response = client.post(
                "/api/v1/permissions",
                headers=headers,
                json={
                    "code": self.permission_code,
                    "description": "Permissão CRUD de integração",
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
                    "description": "Role CRUD de integração",
                },
            )
            self.assertEqual(role_response.status_code, 201)
            self.role_id = UUID(role_response.json()["id"])

            role_detail = client.get(
                f"/api/v1/roles/{self.role_id}",
                headers=headers,
            )
            self.assertEqual(role_detail.status_code, 200)
            self.assertEqual(
                role_detail.json()["name"],
                self.role_name,
            )

            permission_detail = client.get(
                f"/api/v1/permissions/{self.permission_id}",
                headers=headers,
            )
            self.assertEqual(permission_detail.status_code, 200)
            self.assertEqual(
                permission_detail.json()["code"],
                self.permission_code,
            )

            updated_role_name = f"{self.role_name}-updated"
            role_update = client.patch(
                f"/api/v1/roles/{self.role_id}",
                headers=headers,
                json={
                    "name": updated_role_name,
                    "description": None,
                },
            )
            self.assertEqual(role_update.status_code, 200)
            self.assertEqual(
                role_update.json()["name"],
                updated_role_name,
            )
            self.assertIsNone(role_update.json()["description"])

            updated_permission_code = (
                f"{self.permission_code}:updated"
            )
            permission_update = client.patch(
                f"/api/v1/permissions/{self.permission_id}",
                headers=headers,
                json={
                    "code": updated_permission_code,
                    "description": None,
                },
            )
            self.assertEqual(permission_update.status_code, 200)
            self.assertEqual(
                permission_update.json()["code"],
                updated_permission_code,
            )
            self.assertIsNone(
                permission_update.json()["description"]
            )

            role_delete = client.delete(
                f"/api/v1/roles/{self.role_id}",
                headers=headers,
            )
            self.assertEqual(role_delete.status_code, 204)

            deleted_role_detail = client.get(
                f"/api/v1/roles/{self.role_id}",
                headers=headers,
            )
            self.assertEqual(deleted_role_detail.status_code, 404)

            permission_delete = client.delete(
                f"/api/v1/permissions/{self.permission_id}",
                headers=headers,
            )
            self.assertEqual(permission_delete.status_code, 204)

            deleted_permission_detail = client.get(
                f"/api/v1/permissions/{self.permission_id}",
                headers=headers,
            )
            self.assertEqual(
                deleted_permission_detail.status_code,
                404,
            )
