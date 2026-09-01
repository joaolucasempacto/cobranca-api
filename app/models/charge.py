from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, Enum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.base import AuditMixin
from app.models.enums import ChargeStatus


class Charge(AuditMixin, Base):
    __tablename__ = "charges"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_charges_amount_positive"),
    )

    customer_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )
    due_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        default=None,
    )
    status: Mapped[ChargeStatus] = mapped_column(
        Enum(
            ChargeStatus,
            name="charge_status_enum",
            values_callable=lambda enum_class: [
                member.value for member in enum_class
            ],
        ),
        nullable=False,
        default=ChargeStatus.PENDING,
        server_default=ChargeStatus.PENDING.value,
        index=True,
    )

    @classmethod
    def create(
        cls,
        *,
        customer_id: UUID,
        amount: Decimal,
        due_date: date,
        description: str | None = None,
        reference_date: date | None = None,
    ) -> "Charge":
        if amount <= 0:
            raise ValueError("Valor da cobrança deve ser positivo")

        charge = cls(
            customer_id=customer_id,
            amount=amount,
            due_date=due_date,
            description=description,
            status=ChargeStatus.PENDING,
        )
        charge.refresh_status(reference_date)
        return charge

    def update_details(
        self,
        *,
        amount: Decimal | None = None,
        due_date: date | None = None,
        description: str | None = None,
        description_provided: bool = False,
        reference_date: date | None = None,
    ) -> None:
        self._ensure_open("alterada")
        if amount is not None:
            if amount <= 0:
                raise ValueError("Valor da cobrança deve ser positivo")
            self.amount = amount
        if due_date is not None:
            self.due_date = due_date
        if description_provided:
            self.description = description
        self.refresh_status(reference_date)

    def refresh_status(self, reference_date: date | None = None) -> bool:
        if self.status not in {ChargeStatus.PENDING, ChargeStatus.OVERDUE}:
            return False

        current_date = reference_date or date.today()
        expected_status = (
            ChargeStatus.OVERDUE
            if self.due_date < current_date
            else ChargeStatus.PENDING
        )
        if self.status == expected_status:
            return False

        self.status = expected_status
        return True

    def mark_as_paid(self) -> None:
        self._ensure_open("paga")
        self.status = ChargeStatus.PAID

    def cancel(self) -> None:
        self._ensure_open("cancelada")
        self.status = ChargeStatus.CANCELLED

    def soft_delete(self) -> None:
        self.deleted_at = datetime.now(timezone.utc)

    def _ensure_open(self, action: str) -> None:
        if self.status == ChargeStatus.PAID:
            raise ValueError(f"Cobrança paga não pode ser {action}")
        if self.status == ChargeStatus.CANCELLED:
            raise ValueError(f"Cobrança cancelada não pode ser {action}")
