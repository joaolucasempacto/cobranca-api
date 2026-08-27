from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.customer import Customer


class CustomerRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list(self, offset: int, limit: int) -> list[Customer]:
        statement = (
            select(Customer)
            .where(Customer.deleted_at.is_(None))
            .order_by(Customer.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self._session.scalars(statement).all())

    def get_by_id(self, customer_id: UUID) -> Customer | None:
        statement = select(Customer).where(
            Customer.id == customer_id,
            Customer.deleted_at.is_(None),
        )
        return self._session.scalar(statement)

    def exists_by_document(self, document: str) -> bool:
        statement = select(Customer.id).where(Customer.document == document)
        return self._session.scalar(statement) is not None

    def add(self, customer: Customer) -> Customer:
        self._session.add(customer)
        self._session.flush()
        return customer
