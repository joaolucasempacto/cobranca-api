from unittest import TestCase
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.database.session import SessionLocal
from app.main import app
from app.models.associations import role_permissions, user_roles
from app.models.customer import Customer
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User
from app.repositories.unit_of_work import UnitOfWork
from app.services.bootstrap_service import (
    ADMIN_PERMISSIONS,
    ADMIN_ROLE_NAME,
    BootstrapService,
)
from app.services.user_service import UserService


class CustomerHTTPIntegrationTests(TestCase):
    def setUp(self) -> None:
        self.session = SessionLocal()
        unique_value = uuid4().int
        self.admin_email = f"customer-admin-{uuid4()}@example.com"
        self.user_email = f"customer-user-{uuid4()}@example.com"
        self.password = "integration-secret"
        self.document = str(unique_value % 10**11).zfill(11)
        self.admin_id: UUID | None = None
        self.user_id: UUID | None = None
        self.customer_id: UUID | None = None

        self.existing_admin_role_id = self.session.scalar(
            select(Role.id).where(Role.name == ADMIN_ROLE_NAME)
        )
        self.existing_admin_permission_ids = {
            code: self.session.scalar(
                select(Permission.id).where(Permission.code == code)
            )
            for code, _ in ADMIN_PERMISSIONS
        }

        uow = UnitOfWork(self.session)
        admin = BootstrapService(uow).bootstrap_admin(
            self.admin_email,
            self.password,
        )
        self.admin_id = admin.id
        user = UserService(uow).create(
            email=self.user_email,
            password=self.password,
        )
        self.user_id = user.id

    def tearDown(self) -> None:
        self.session.rollback()
        self.session.execute(
            delete(Customer).where(Customer.document == self.document)
        )

        user_ids = [
            user_id
            for user_id in (self.admin_id, self.user_id)
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

    def _login(self, client: TestClient, email: str) -> dict[str, str]:
        response = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": self.password},
        )
        self.assertEqual(response.status_code, 200)
        return {
            "Authorization": f"Bearer {response.json()['access_token']}"
        }

    def test_customer_crud_and_rbac_flow(self) -> None:
        with TestClient(app) as client:
            admin_headers = self._login(client, self.admin_email)
            user_headers = self._login(client, self.user_email)

            forbidden_response = client.get(
                "/api/v1/customers",
                headers=user_headers,
            )
            self.assertEqual(forbidden_response.status_code, 403)

            formatted_document = (
                f"{self.document[:3]}.{self.document[3:6]}."
                f"{self.document[6:9]}-{self.document[9:]}"
            )
            create_response = client.post(
                "/api/v1/customers",
                headers=admin_headers,
                json={
                    "name": "Cliente de Integração",
                    "document": formatted_document,
                    "email": "customer@example.com",
                    "phone": "11999999999",
                    "address": "Rua Principal, 10",
                },
            )
            self.assertEqual(create_response.status_code, 201)
            created = create_response.json()
            self.customer_id = UUID(created["id"])
            self.assertEqual(created["document"], self.document)

            duplicate_response = client.post(
                "/api/v1/customers",
                headers=admin_headers,
                json={
                    "name": "Cliente Duplicado",
                    "document": self.document,
                },
            )
            self.assertEqual(duplicate_response.status_code, 409)

            list_response = client.get(
                "/api/v1/customers?offset=0&limit=10",
                headers=admin_headers,
            )
            self.assertEqual(list_response.status_code, 200)
            self.assertIn(
                str(self.customer_id),
                {item["id"] for item in list_response.json()},
            )

            detail_response = client.get(
                f"/api/v1/customers/{self.customer_id}",
                headers=admin_headers,
            )
            self.assertEqual(detail_response.status_code, 200)

            update_response = client.patch(
                f"/api/v1/customers/{self.customer_id}",
                headers=admin_headers,
                json={
                    "name": "Cliente Atualizado",
                    "email": None,
                    "address": None,
                },
            )
            self.assertEqual(update_response.status_code, 200)
            updated = update_response.json()
            self.assertEqual(updated["name"], "Cliente Atualizado")
            self.assertIsNone(updated["email"])
            self.assertIsNone(updated["address"])

            delete_response = client.delete(
                f"/api/v1/customers/{self.customer_id}",
                headers=admin_headers,
            )
            self.assertEqual(delete_response.status_code, 204)

            missing_response = client.get(
                f"/api/v1/customers/{self.customer_id}",
                headers=admin_headers,
            )
            self.assertEqual(missing_response.status_code, 404)

            reused_document_response = client.post(
                "/api/v1/customers",
                headers=admin_headers,
                json={
                    "name": "Cliente Reutilizado",
                    "document": self.document,
                },
            )
            self.assertEqual(reused_document_response.status_code, 409)
