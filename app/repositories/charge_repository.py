from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.charge import Charge


class ChargeRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list(self, offset: int, limit: int) -> list[Charge]:
        statement = (
            select(Charge)
            .where(Charge.deleted_at.is_(None))
            .order_by(Charge.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self._session.scalars(statement).all())

    def get_by_id(self, charge_id: UUID) -> Charge | None:
        statement = select(Charge).where(
            Charge.id == charge_id,
            Charge.deleted_at.is_(None),
        )
        return self._session.scalar(statement)

    def add(self, charge: Charge) -> Charge:
        self._session.add(charge)
        self._session.flush()
        return charge
