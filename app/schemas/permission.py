from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PermissionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=255)


class PermissionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def require_update_value(self) -> "PermissionUpdate":
        description_provided = "description" in self.model_fields_set
        if self.code is None and not description_provided:
            raise ValueError("Informe ao menos um campo para atualização")
        return self


class PermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    description: str | None
    created_at: datetime
    updated_at: datetime
