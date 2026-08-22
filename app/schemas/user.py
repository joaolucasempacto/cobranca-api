from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=128)
    is_active: bool = True


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str | None = Field(default=None, min_length=3, max_length=320)
    password: str | None = Field(default=None, min_length=1, max_length=128)
    is_active: bool | None = None

    @model_validator(mode="after")
    def require_change(self) -> "UserUpdate":
        if not self.model_fields_set:
            raise ValueError("Informe ao menos um campo para atualização")
        return self


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
