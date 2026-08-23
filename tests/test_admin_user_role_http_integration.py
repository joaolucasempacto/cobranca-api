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


class AdministrativeUserRoleHTTPIntegrationTests(TestCase):
    def setUp(self) -> None:
        self.session = SessionLocal()
        self.admin_email = f"admin-user-role-{uuid4()}@example.com"
        self.user_email = f"managed-user-role-{uuid4()}@example.com"
        self.role_name = f"managed-role-{uuid4()}"
        self.password = "integration-secret"
        self.admin_id: UUID | None = None

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
        ).bootstrap_admin(self.admin_email, self.password)
        self.admin_id = admin.id

    def tearDown(self) -> None:
        self.session.rollback()

        role = self.session.scalar(
            select(Role).where(Role.name == self.role_name)
        )
        if role is not None:
            self.session.execute(
                delete(user_roles).where(user_roles.c.role_id == role.id)
            )
            self.session.execute(
                delete(role_permissions).where(
                    role_permissions.c.role_id == role.id
                )
            )
            self.session.delete(role)

        managed_user = self.session.scalar(
            select(User).where(User.email == self.user_email)
        )
        user_ids = [
            user_id
            for user_id in (
                managed_user.id if managed_user is not None else None,
                self.admin_id,
            )
            if user_id is not None
        ]
        if user_ids:
            self.session.execute(
                delete(user_roles).where(user_roles.c.user_id.in_(user_ids))
            )
            self.session.execute(delete(User).where(User.id.in_(user_ids)))

        admin_role = self.session.scalar(
            select(Role).where(Role.name == ADMIN_ROLE_NAME)
        )
        if self.existing_admin_role_id is None and admin_role is not None:
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

    def test_user_role_grant_list_and_revoke_flow(self) -> None:
        with TestClient(app) as client:
            login_response = client.post(
                "/api/v1/auth/login",
                json={"email": self.admin_email, "password": self.password},
            )
            self.assertEqual(login_response.status_code, 200)
            headers = {
                "Authorization": (
                    f"Bearer {login_response.json()['access_token']}"
                )
            }

            user_response = client.post(
                "/api/v1/users",
                headers=headers,
                json={
                    "email": self.user_email,
                    "password": "managed-secret",
                    "is_active": True,
                },
            )
            self.assertEqual(user_response.status_code, 201)
            user_id = UUID(user_response.json()["id"])

            role_response = client.post(
                "/api/v1/roles",
                headers=headers,
                json={
                    "name": self.role_name,
                    "description": "Role de integração de usuário",
                },
            )
            self.assertEqual(role_response.status_code, 201)
            role_id = UUID(role_response.json()["id"])

            grant_response = client.put(
                f"/api/v1/users/{user_id}/roles/{role_id}",
                headers=headers,
            )
            self.assertEqual(grant_response.status_code, 204)

            list_response = client.get(
                f"/api/v1/users/{user_id}/roles",
                headers=headers,
            )
            self.assertEqual(list_response.status_code, 200)
            self.assertIn(
                self.role_name,
                {item["name"] for item in list_response.json()},
            )

            revoke_response = client.delete(
                f"/api/v1/users/{user_id}/roles/{role_id}",
                headers=headers,
            )
            self.assertEqual(revoke_response.status_code, 204)

            empty_response = client.get(
                f"/api/v1/users/{user_id}/roles",
                headers=headers,
            )
            self.assertEqual(empty_response.status_code, 200)
            self.assertEqual(empty_response.json(), [])
