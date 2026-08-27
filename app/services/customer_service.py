from uuid import UUID

from app.exceptions.base import ConflictError, NotFoundError
from app.models.customer import Customer
from app.repositories.unit_of_work import UnitOfWork


class CustomerService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def list_customers(self, offset: int, limit: int) -> list[Customer]:
        return self._uow.customers.list(offset=offset, limit=limit)

    def get_by_id(self, customer_id: UUID) -> Customer:
        customer = self._uow.customers.get_by_id(customer_id)
        if customer is None:
            raise NotFoundError("Cliente não encontrado")
        return customer

    def create(
        self,
        *,
        name: str,
        document: str,
        email: str | None = None,
        phone: str | None = None,
        address: str | None = None,
    ) -> Customer:
        if self._uow.customers.exists_by_document(document):
            raise ConflictError("Documento já cadastrado")

        customer = Customer(
            name=name,
            document=document,
            email=email,
            phone=phone,
            address=address,
        )
        added_customer = self._uow.customers.add(customer)
        self._uow.commit()
        return added_customer

    def update(
        self,
        customer_id: UUID,
        *,
        name: str | None = None,
        document: str | None = None,
        email: str | None = None,
        email_provided: bool = False,
        phone: str | None = None,
        phone_provided: bool = False,
        address: str | None = None,
        address_provided: bool = False,
    ) -> Customer:
        customer = self.get_by_id(customer_id)
        if (
            document is not None
            and document != customer.document
            and self._uow.customers.exists_by_document(document)
        ):
            raise ConflictError("Documento já cadastrado")

        customer.update_details(
            name=name,
            document=document,
            email=email,
            email_provided=email_provided,
            phone=phone,
            phone_provided=phone_provided,
            address=address,
            address_provided=address_provided,
        )
        self._uow.commit()
        return customer

    def delete(self, customer_id: UUID) -> None:
        customer = self.get_by_id(customer_id)
        customer.soft_delete()
        self._uow.commit()
