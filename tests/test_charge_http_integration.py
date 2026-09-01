from datetime import date, timedelta
from unittest import TestCase
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.database.session import SessionLocal
from app.main import app
from app.models.associations import role_permissions, user_roles
from app.models.charge import Charge
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
from app.services.customer_service import CustomerService
from app.services.user_service import UserService


class ChargeHTTPIntegrationTests(TestCase):
    def setUp(self) -> None:
        self.session = SessionLocal()
        self.admin_email = f"charge-admin-{uuid4()}@example.com"
        self.user_email = f"charge-user-{uuid4()}@example.com"
        self.password = "integration-secret"
        self.document = str(uuid4().int % 10**11).zfill(11)
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
        customer = CustomerService(uow).create(
            name="Cliente da Cobrança",
            document=self.document,
        )
        self.customer_id = customer.id

    def tearDown(self) -> None:
        self.session.rollback()
        if self.customer_id is not None:
            self.session.execute(
                delete(Charge).where(Charge.customer_id == self.customer_id)
            )
            self.session.execute(
                delete(Customer).where(Customer.id == self.customer_id)
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

    def test_charge_crud_status_and_rbac_flow(self) -> None:
        assert self.customer_id is not None
        with TestClient(app) as client:
            admin_headers = self._login(client, self.admin_email)
            user_headers = self._login(client, self.user_email)

            forbidden_response = client.get(
                "/api/v1/charges",
                headers=user_headers,
            )
            self.assertEqual(forbidden_response.status_code, 403)

            missing_customer_response = client.post(
                "/api/v1/charges",
                headers=admin_headers,
                json={
                    "customer_id": str(uuid4()),
                    "amount": "100.00",
                    "due_date": str(date.today()),
                },
            )
            self.assertEqual(missing_customer_response.status_code, 404)

            create_response = client.post(
                "/api/v1/charges",
                headers=admin_headers,
                json={
                    "customer_id": str(self.customer_id),
                    "amount": "150.75",
                    "due_date": str(date.today() + timedelta(days=10)),
                    "description": "Mensalidade",
                },
            )
            self.assertEqual(create_response.status_code, 201)
            created = create_response.json()
            charge_id = UUID(created["id"])
            self.assertEqual(created["amount"], "150.75")
            self.assertEqual(created["status"], "pending")

            overdue_response = client.post(
                "/api/v1/charges",
                headers=admin_headers,
                json={
                    "customer_id": str(self.customer_id),
                    "amount": "80.00",
                    "due_date": str(date.today() - timedelta(days=1)),
                },
            )
            self.assertEqual(overdue_response.status_code, 201)
            self.assertEqual(overdue_response.json()["status"], "overdue")

            list_response = client.get(
                "/api/v1/charges?offset=0&limit=10",
                headers=admin_headers,
            )
            self.assertEqual(list_response.status_code, 200)
            self.assertIn(
                str(charge_id),
                {item["id"] for item in list_response.json()},
            )

            detail_response = client.get(
                f"/api/v1/charges/{charge_id}",
                headers=admin_headers,
            )
            self.assertEqual(detail_response.status_code, 200)

            update_response = client.patch(
                f"/api/v1/charges/{charge_id}",
                headers=admin_headers,
                json={"amount": "175.25", "description": None},
            )
            self.assertEqual(update_response.status_code, 200)
            self.assertEqual(update_response.json()["amount"], "175.25")
            self.assertIsNone(update_response.json()["description"])

            cancel_response = client.post(
                f"/api/v1/charges/{charge_id}/cancel",
                headers=admin_headers,
            )
            self.assertEqual(cancel_response.status_code, 200)
            self.assertEqual(cancel_response.json()["status"], "cancelled")

            immutable_response = client.patch(
                f"/api/v1/charges/{charge_id}",
                headers=admin_headers,
                json={"amount": "200.00"},
            )
            self.assertEqual(immutable_response.status_code, 409)

            delete_response = client.delete(
                f"/api/v1/charges/{charge_id}",
                headers=admin_headers,
            )
            self.assertEqual(delete_response.status_code, 204)

            missing_response = client.get(
                f"/api/v1/charges/{charge_id}",
                headers=admin_headers,
            )
            self.assertEqual(missing_response.status_code, 404)
