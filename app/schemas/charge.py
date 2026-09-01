from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import ChargeStatus


class ChargeCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    customer_id: UUID
    amount: Decimal = Field(
        gt=Decimal("0"),
        max_digits=12,
        decimal_places=2,
    )
    due_date: date
    description: str | None = Field(default=None, min_length=1, max_length=255)


class ChargeUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    amount: Decimal | None = Field(
        default=None,
        gt=Decimal("0"),
        max_digits=12,
        decimal_places=2,
    )
    due_date: date | None = None
    description: str | None = Field(default=None, min_length=1, max_length=255)

    @model_validator(mode="after")
    def require_update_value(self) -> "ChargeUpdate":
        if not self.model_fields_set:
            raise ValueError("Informe ao menos um campo para atualização")
        if "amount" in self.model_fields_set and self.amount is None:
            raise ValueError("Valor não pode ser nulo")
        if "due_date" in self.model_fields_set and self.due_date is None:
            raise ValueError("Vencimento não pode ser nulo")
        return self


class ChargeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    customer_id: UUID
    amount: Decimal
    due_date: date
    description: str | None
    status: ChargeStatus
    created_at: datetime
    updated_at: datetime
