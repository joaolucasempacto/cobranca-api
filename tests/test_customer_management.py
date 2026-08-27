from datetime import datetime, timezone
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock
from uuid import uuid4

from pydantic import ValidationError

from app.exceptions.base import ConflictError, NotFoundError
from app.models.customer import Customer
from app.routers.customers import (
    create_customer,
    delete_customer,
    get_customer,
    list_customers,
    router,
    update_customer,
)
from app.schemas.customer import CustomerCreate, CustomerUpdate
from app.services.customer_service import CustomerService


class CustomerModelTests(TestCase):
    def test_update_details_changes_and_clears_optional_fields(self) -> None:
        customer = Customer(
            name="Cliente Original",
            document="12345678901",
            email="old@example.com",
            phone="11999999999",
            address="Endereço antigo",
        )

        customer.update_details(
            name="Cliente Atualizado",
            document="12345678000199",
            email=None,
            email_provided=True,
            phone=None,
            phone_provided=True,
            address=None,
            address_provided=True,
        )

        self.assertEqual(customer.name, "Cliente Atualizado")
        self.assertEqual(customer.document, "12345678000199")
        self.assertIsNone(customer.email)
        self.assertIsNone(customer.phone)
        self.assertIsNone(customer.address)

    def test_soft_delete_marks_customer_with_timezone(self) -> None:
        customer = Customer(name="Cliente", document="12345678901")

        customer.soft_delete()

        self.assertIsNotNone(customer.deleted_at)
        assert customer.deleted_at is not None
        self.assertIsNotNone(customer.deleted_at.tzinfo)


class CustomerSchemaTests(TestCase):
    def test_create_normalizes_cpf_and_cnpj(self) -> None:
        cpf = CustomerCreate(
            name="Pessoa Física",
            document="123.456.789-01",
        )
        cnpj = CustomerCreate(
            name="Pessoa Jurídica",
            document="12.345.678/0001-99",
        )

        self.assertEqual(cpf.document, "12345678901")
        self.assertEqual(cnpj.document, "12345678000199")

    def test_create_rejects_invalid_document_format(self) -> None:
        with self.assertRaises(ValidationError):
            CustomerCreate(name="Cliente", document="abc12345678901")

        with self.assertRaises(ValidationError):
            CustomerCreate(name="Cliente", document="123")

    def test_create_rejects_invalid_email(self) -> None:
        with self.assertRaises(ValidationError):
            CustomerCreate(
                name="Cliente",
                document="12345678901",
                email="invalid-email",
            )

    def test_update_requires_at_least_one_field(self) -> None:
        with self.assertRaises(ValidationError):
            CustomerUpdate()

    def test_update_allows_clearing_optional_fields(self) -> None:
        payload = CustomerUpdate(email=None, phone=None, address=None)

        self.assertEqual(
            payload.model_fields_set,
            {"email", "phone", "address"},
        )

    def test_update_rejects_null_required_fields(self) -> None:
        with self.assertRaises(ValidationError):
            CustomerUpdate(name=None)

        with self.assertRaises(ValidationError):
            CustomerUpdate(document=None)


class CustomerServiceTests(TestCase):
    def test_create_persists_and_commits(self) -> None:
        uow = Mock()
        uow.customers.exists_by_document.return_value = False
        created = Mock()
        uow.customers.add.return_value = created

        result = CustomerService(uow).create(
            name="Cliente",
            document="12345678901",
            email="cliente@example.com",
            phone="11999999999",
            address="Rua Principal, 10",
        )

        self.assertIs(result, created)
        customer = uow.customers.add.call_args.args[0]
        self.assertEqual(customer.name, "Cliente")
        self.assertEqual(customer.document, "12345678901")
        self.assertEqual(customer.email, "cliente@example.com")
        uow.commit.assert_called_once_with()

    def test_create_rejects_duplicate_document(self) -> None:
        uow = Mock()
        uow.customers.exists_by_document.return_value = True

        with self.assertRaisesRegex(
            ConflictError,
            "Documento já cadastrado",
        ):
            CustomerService(uow).create(
                name="Cliente",
                document="12345678901",
            )

        uow.customers.add.assert_not_called()
        uow.commit.assert_not_called()

    def test_get_rejects_missing_customer(self) -> None:
        uow = Mock()
        uow.customers.get_by_id.return_value = None

        with self.assertRaisesRegex(NotFoundError, "Cliente não encontrado"):
            CustomerService(uow).get_by_id(uuid4())

    def test_list_delegates_pagination(self) -> None:
        uow = Mock()
        expected = [Mock(), Mock()]
        uow.customers.list.return_value = expected

        result = CustomerService(uow).list_customers(offset=10, limit=25)

        self.assertEqual(result, expected)
        uow.customers.list.assert_called_once_with(offset=10, limit=25)

    def test_update_rejects_duplicate_document(self) -> None:
        customer_id = uuid4()
        customer = SimpleNamespace(document="12345678901")
        uow = Mock()
        uow.customers.get_by_id.return_value = customer
        uow.customers.exists_by_document.return_value = True

        with self.assertRaisesRegex(
            ConflictError,
            "Documento já cadastrado",
        ):
            CustomerService(uow).update(
                customer_id,
                document="12345678000199",
            )

        uow.commit.assert_not_called()

    def test_update_delegates_domain_changes_and_commits(self) -> None:
        customer_id = uuid4()
        customer = Mock(document="12345678901")
        uow = Mock()
        uow.customers.get_by_id.return_value = customer

        result = CustomerService(uow).update(
            customer_id,
            name="Novo nome",
            email=None,
            email_provided=True,
        )

        self.assertIs(result, customer)
        customer.update_details.assert_called_once_with(
            name="Novo nome",
            document=None,
            email=None,
            email_provided=True,
            phone=None,
            phone_provided=False,
            address=None,
            address_provided=False,
        )
        uow.commit.assert_called_once_with()

    def test_delete_soft_deletes_and_commits(self) -> None:
        customer_id = uuid4()
        customer = Mock()
        uow = Mock()
        uow.customers.get_by_id.return_value = customer

        CustomerService(uow).delete(customer_id)

        customer.soft_delete.assert_called_once_with()
        uow.commit.assert_called_once_with()


class CustomerRouterTests(TestCase):
    def setUp(self) -> None:
        self.now = datetime.now(timezone.utc)
        self.customer_id = uuid4()
        self.customer = SimpleNamespace(
            id=self.customer_id,
            name="Cliente",
            document="12345678901",
            email="cliente@example.com",
            phone="11999999999",
            address="Rua Principal, 10",
            created_at=self.now,
            updated_at=self.now,
        )

    def test_router_delegates_crud_to_service(self) -> None:
        service = Mock()
        service.create.return_value = self.customer
        service.list_customers.return_value = [self.customer]
        service.get_by_id.return_value = self.customer
        service.update.return_value = self.customer

        created = create_customer(
            CustomerCreate(
                name="Cliente",
                document="123.456.789-01",
                email="cliente@example.com",
                phone="11999999999",
                address="Rua Principal, 10",
            ),
            service,
            Mock(),
        )
        listed = list_customers(service, Mock(), offset=0, limit=50)
        detailed = get_customer(self.customer_id, service, Mock())
        updated = update_customer(
            self.customer_id,
            CustomerUpdate(email=None),
            service,
            Mock(),
        )
        deleted = delete_customer(self.customer_id, service, Mock())

        self.assertEqual(created.id, self.customer_id)
        self.assertEqual([item.id for item in listed], [self.customer_id])
        self.assertEqual(detailed.id, self.customer_id)
        self.assertEqual(updated.id, self.customer_id)
        self.assertEqual(deleted.status_code, 204)
        service.create.assert_called_once_with(
            name="Cliente",
            document="12345678901",
            email="cliente@example.com",
            phone="11999999999",
            address="Rua Principal, 10",
        )
        service.list_customers.assert_called_once_with(offset=0, limit=50)
        service.get_by_id.assert_called_once_with(self.customer_id)
        service.update.assert_called_once_with(
            self.customer_id,
            name=None,
            document=None,
            email=None,
            email_provided=True,
            phone=None,
            phone_provided=False,
            address=None,
            address_provided=False,
        )
        service.delete.assert_called_once_with(self.customer_id)

    def test_router_exposes_customer_crud_routes(self) -> None:
        routes = {
            (route.path, tuple(sorted(route.methods or set())))
            for route in router.routes
        }

        self.assertIn(("/customers", ("GET",)), routes)
        self.assertIn(("/customers", ("POST",)), routes)
        self.assertIn(("/customers/{customer_id}", ("GET",)), routes)
        self.assertIn(("/customers/{customer_id}", ("PATCH",)), routes)
        self.assertIn(("/customers/{customer_id}", ("DELETE",)), routes)
