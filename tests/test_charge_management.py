from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock
from uuid import uuid4

from pydantic import ValidationError

from app.exceptions.base import ConflictError, NotFoundError
from app.models.charge import Charge
from app.models.enums import ChargeStatus
from app.routers.charges import (
    cancel_charge,
    create_charge,
    delete_charge,
    get_charge,
    list_charges,
    router,
    update_charge,
)
from app.schemas.charge import ChargeCreate, ChargeUpdate
from app.services.charge_service import ChargeService


class ChargeModelTests(TestCase):
    def setUp(self) -> None:
        self.customer_id = uuid4()
        self.today = date(2026, 9, 1)

    def test_factory_sets_pending_or_overdue_status(self) -> None:
        pending = Charge.create(
            customer_id=self.customer_id,
            amount=Decimal("150.00"),
            due_date=self.today + timedelta(days=1),
            reference_date=self.today,
        )
        overdue = Charge.create(
            customer_id=self.customer_id,
            amount=Decimal("75.50"),
            due_date=self.today - timedelta(days=1),
            reference_date=self.today,
        )

        self.assertEqual(pending.status, ChargeStatus.PENDING)
        self.assertEqual(overdue.status, ChargeStatus.OVERDUE)

    def test_factory_rejects_non_positive_amount(self) -> None:
        with self.assertRaisesRegex(ValueError, "deve ser positivo"):
            Charge.create(
                customer_id=self.customer_id,
                amount=Decimal("0"),
                due_date=self.today,
                reference_date=self.today,
            )

    def test_update_recalculates_due_status_and_clears_description(self) -> None:
        charge = Charge.create(
            customer_id=self.customer_id,
            amount=Decimal("100.00"),
            due_date=self.today - timedelta(days=1),
            description="Original",
            reference_date=self.today,
        )

        charge.update_details(
            amount=Decimal("125.00"),
            due_date=self.today + timedelta(days=5),
            description=None,
            description_provided=True,
            reference_date=self.today,
        )

        self.assertEqual(charge.amount, Decimal("125.00"))
        self.assertIsNone(charge.description)
        self.assertEqual(charge.status, ChargeStatus.PENDING)

    def test_paid_charge_cannot_be_changed_or_cancelled(self) -> None:
        charge = Charge.create(
            customer_id=self.customer_id,
            amount=Decimal("100.00"),
            due_date=self.today,
            reference_date=self.today,
        )

        charge.mark_as_paid()

        self.assertEqual(charge.status, ChargeStatus.PAID)
        with self.assertRaisesRegex(ValueError, "paga não pode ser alterada"):
            charge.update_details(amount=Decimal("200.00"))
        with self.assertRaisesRegex(ValueError, "paga não pode ser cancelada"):
            charge.cancel()

    def test_cancelled_charge_cannot_be_marked_as_paid(self) -> None:
        charge = Charge.create(
            customer_id=self.customer_id,
            amount=Decimal("100.00"),
            due_date=self.today,
            reference_date=self.today,
        )

        charge.cancel()

        self.assertEqual(charge.status, ChargeStatus.CANCELLED)
        with self.assertRaisesRegex(ValueError, "cancelada não pode ser paga"):
            charge.mark_as_paid()

    def test_soft_delete_marks_charge_with_timezone(self) -> None:
        charge = Charge.create(
            customer_id=self.customer_id,
            amount=Decimal("100.00"),
            due_date=self.today,
            reference_date=self.today,
        )

        charge.soft_delete()

        self.assertIsNotNone(charge.deleted_at)
        assert charge.deleted_at is not None
        self.assertIsNotNone(charge.deleted_at.tzinfo)


class ChargeSchemaTests(TestCase):
    def test_create_accepts_precise_monetary_value(self) -> None:
        payload = ChargeCreate(
            customer_id=uuid4(),
            amount="1234.56",
            due_date="2026-09-30",
        )

        self.assertEqual(payload.amount, Decimal("1234.56"))
        self.assertEqual(payload.due_date, date(2026, 9, 30))

    def test_create_rejects_invalid_amounts(self) -> None:
        for amount in ("0", "-1", "10.999", "12345678901.00"):
            with self.subTest(amount=amount):
                with self.assertRaises(ValidationError):
                    ChargeCreate(
                        customer_id=uuid4(),
                        amount=amount,
                        due_date="2026-09-30",
                    )

    def test_update_requires_a_field(self) -> None:
        with self.assertRaises(ValidationError):
            ChargeUpdate()

    def test_update_allows_clearing_description(self) -> None:
        payload = ChargeUpdate(description=None)

        self.assertEqual(payload.model_fields_set, {"description"})

    def test_update_rejects_null_required_fields(self) -> None:
        with self.assertRaises(ValidationError):
            ChargeUpdate(amount=None)

        with self.assertRaises(ValidationError):
            ChargeUpdate(due_date=None)


class ChargeServiceTests(TestCase):
    def setUp(self) -> None:
        self.today = date(2026, 9, 1)
        self.customer_id = uuid4()

    def test_create_requires_existing_customer(self) -> None:
        uow = Mock()
        uow.customers.get_by_id.return_value = None

        with self.assertRaisesRegex(NotFoundError, "Cliente não encontrado"):
            ChargeService(uow).create(
                customer_id=self.customer_id,
                amount=Decimal("100.00"),
                due_date=self.today,
            )

        uow.charges.add.assert_not_called()
        uow.commit.assert_not_called()

    def test_create_persists_and_commits(self) -> None:
        uow = Mock()
        uow.customers.get_by_id.return_value = Mock()
        created = Mock()
        uow.charges.add.return_value = created

        result = ChargeService(uow).create(
            customer_id=self.customer_id,
            amount=Decimal("100.00"),
            due_date=self.today,
            description="Mensalidade",
            reference_date=self.today,
        )

        self.assertIs(result, created)
        charge = uow.charges.add.call_args.args[0]
        self.assertEqual(charge.customer_id, self.customer_id)
        self.assertEqual(charge.amount, Decimal("100.00"))
        self.assertEqual(charge.status, ChargeStatus.PENDING)
        uow.commit.assert_called_once_with()

    def test_list_refreshes_every_charge_and_commits_once(self) -> None:
        uow = Mock()
        first = Mock()
        second = Mock()
        first.refresh_status.return_value = True
        second.refresh_status.return_value = True
        uow.charges.list.return_value = [first, second]

        result = ChargeService(uow).list_charges(
            offset=5,
            limit=20,
            reference_date=self.today,
        )

        self.assertEqual(result, [first, second])
        first.refresh_status.assert_called_once_with(self.today)
        second.refresh_status.assert_called_once_with(self.today)
        uow.commit.assert_called_once_with()

    def test_get_refreshes_overdue_status(self) -> None:
        charge_id = uuid4()
        charge = Mock()
        charge.refresh_status.return_value = True
        uow = Mock()
        uow.charges.get_by_id.return_value = charge

        result = ChargeService(uow).get_by_id(
            charge_id,
            reference_date=self.today,
        )

        self.assertIs(result, charge)
        charge.refresh_status.assert_called_once_with(self.today)
        uow.commit.assert_called_once_with()

    def test_get_rejects_missing_charge(self) -> None:
        uow = Mock()
        uow.charges.get_by_id.return_value = None

        with self.assertRaisesRegex(NotFoundError, "Cobrança não encontrada"):
            ChargeService(uow).get_by_id(uuid4())

    def test_update_maps_domain_conflict(self) -> None:
        charge = Mock()
        charge.update_details.side_effect = ValueError(
            "Cobrança paga não pode ser alterada"
        )
        uow = Mock()
        uow.charges.get_by_id.return_value = charge

        with self.assertRaisesRegex(ConflictError, "paga não pode"):
            ChargeService(uow).update(
                uuid4(),
                amount=Decimal("200.00"),
            )

        uow.commit.assert_not_called()

    def test_cancel_delegates_transition_and_commits(self) -> None:
        charge_id = uuid4()
        charge = Mock()
        uow = Mock()
        uow.charges.get_by_id.return_value = charge

        result = ChargeService(uow).cancel(charge_id)

        self.assertIs(result, charge)
        charge.refresh_status.assert_called_once_with()
        charge.cancel.assert_called_once_with()
        uow.commit.assert_called_once_with()

    def test_delete_soft_deletes_and_commits(self) -> None:
        charge = Mock()
        uow = Mock()
        uow.charges.get_by_id.return_value = charge

        ChargeService(uow).delete(uuid4())

        charge.soft_delete.assert_called_once_with()
        uow.commit.assert_called_once_with()


class ChargeRouterTests(TestCase):
    def setUp(self) -> None:
        self.charge_id = uuid4()
        self.customer_id = uuid4()
        self.now = datetime.now(timezone.utc)
        self.charge = SimpleNamespace(
            id=self.charge_id,
            customer_id=self.customer_id,
            amount=Decimal("100.00"),
            due_date=date(2026, 9, 30),
            description="Mensalidade",
            status=ChargeStatus.PENDING,
            created_at=self.now,
            updated_at=self.now,
        )

    def test_router_delegates_crud_and_cancel(self) -> None:
        service = Mock()
        service.create.return_value = self.charge
        service.list_charges.return_value = [self.charge]
        service.get_by_id.return_value = self.charge
        service.update.return_value = self.charge
        service.cancel.return_value = self.charge

        created = create_charge(
            ChargeCreate(
                customer_id=self.customer_id,
                amount="100.00",
                due_date="2026-09-30",
                description="Mensalidade",
            ),
            service,
            Mock(),
        )
        listed = list_charges(service, Mock(), offset=0, limit=50)
        detailed = get_charge(self.charge_id, service, Mock())
        updated = update_charge(
            self.charge_id,
            ChargeUpdate(description=None),
            service,
            Mock(),
        )
        cancelled = cancel_charge(self.charge_id, service, Mock())
        deleted = delete_charge(self.charge_id, service, Mock())

        self.assertEqual(created.id, self.charge_id)
        self.assertEqual([item.id for item in listed], [self.charge_id])
        self.assertEqual(detailed.id, self.charge_id)
        self.assertEqual(updated.id, self.charge_id)
        self.assertEqual(cancelled.id, self.charge_id)
        self.assertEqual(deleted.status_code, 204)
        service.create.assert_called_once_with(
            customer_id=self.customer_id,
            amount=Decimal("100.00"),
            due_date=date(2026, 9, 30),
            description="Mensalidade",
        )
        service.list_charges.assert_called_once_with(offset=0, limit=50)
        service.get_by_id.assert_called_once_with(self.charge_id)
        service.update.assert_called_once_with(
            self.charge_id,
            amount=None,
            due_date=None,
            description=None,
            description_provided=True,
        )
        service.cancel.assert_called_once_with(self.charge_id)
        service.delete.assert_called_once_with(self.charge_id)

    def test_router_exposes_charge_routes(self) -> None:
        routes = {
            (route.path, tuple(sorted(route.methods or set())))
            for route in router.routes
        }

        self.assertIn(("/charges", ("GET",)), routes)
        self.assertIn(("/charges", ("POST",)), routes)
        self.assertIn(("/charges/{charge_id}", ("GET",)), routes)
        self.assertIn(("/charges/{charge_id}", ("PATCH",)), routes)
        self.assertIn(("/charges/{charge_id}/cancel", ("POST",)), routes)
        self.assertIn(("/charges/{charge_id}", ("DELETE",)), routes)
