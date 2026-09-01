from datetime import date
from decimal import Decimal
from uuid import UUID

from app.exceptions.base import ConflictError, NotFoundError
from app.models.charge import Charge
from app.repositories.unit_of_work import UnitOfWork


class ChargeService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def list_charges(
        self,
        offset: int,
        limit: int,
        reference_date: date | None = None,
    ) -> list[Charge]:
        charges = self._uow.charges.list(offset=offset, limit=limit)
        status_changed = False
        for charge in charges:
            status_changed = (
                charge.refresh_status(reference_date) or status_changed
            )
        if status_changed:
            self._uow.commit()
        return charges

    def get_by_id(
        self,
        charge_id: UUID,
        reference_date: date | None = None,
    ) -> Charge:
        charge = self._get_by_id(charge_id)
        if charge.refresh_status(reference_date):
            self._uow.commit()
        return charge

    def create(
        self,
        *,
        customer_id: UUID,
        amount: Decimal,
        due_date: date,
        description: str | None = None,
        reference_date: date | None = None,
    ) -> Charge:
        if self._uow.customers.get_by_id(customer_id) is None:
            raise NotFoundError("Cliente não encontrado")

        try:
            charge = Charge.create(
                customer_id=customer_id,
                amount=amount,
                due_date=due_date,
                description=description,
                reference_date=reference_date,
            )
        except ValueError as exc:
            raise ConflictError(str(exc)) from exc

        added_charge = self._uow.charges.add(charge)
        self._uow.commit()
        return added_charge

    def update(
        self,
        charge_id: UUID,
        *,
        amount: Decimal | None = None,
        due_date: date | None = None,
        description: str | None = None,
        description_provided: bool = False,
        reference_date: date | None = None,
    ) -> Charge:
        charge = self._get_by_id(charge_id)
        try:
            charge.update_details(
                amount=amount,
                due_date=due_date,
                description=description,
                description_provided=description_provided,
                reference_date=reference_date,
            )
        except ValueError as exc:
            raise ConflictError(str(exc)) from exc
        self._uow.commit()
        return charge

    def cancel(self, charge_id: UUID) -> Charge:
        charge = self._get_by_id(charge_id)
        try:
            charge.refresh_status()
            charge.cancel()
        except ValueError as exc:
            raise ConflictError(str(exc)) from exc
        self._uow.commit()
        return charge

    def delete(self, charge_id: UUID) -> None:
        charge = self._get_by_id(charge_id)
        charge.soft_delete()
        self._uow.commit()

    def _get_by_id(self, charge_id: UUID) -> Charge:
        charge = self._uow.charges.get_by_id(charge_id)
        if charge is None:
            raise NotFoundError("Cobrança não encontrada")
        return charge
