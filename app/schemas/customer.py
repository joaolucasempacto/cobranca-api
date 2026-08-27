from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)


def normalize_document(document: str) -> str:
    allowed_formatting = {".", "-", "/", " "}
    if any(
        not character.isdigit() and character not in allowed_formatting
        for character in document
    ):
        raise ValueError("Documento deve conter apenas números")

    digits = "".join(character for character in document if character.isdigit())
    if len(digits) not in {11, 14}:
        raise ValueError("Documento deve ser um CPF ou CNPJ")
    return digits


class CustomerCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=200)
    document: str
    email: EmailStr | None = None
    phone: str | None = Field(default=None, min_length=1, max_length=20)
    address: str | None = Field(default=None, min_length=1, max_length=255)

    @field_validator("document")
    @classmethod
    def validate_document(cls, document: str) -> str:
        return normalize_document(document)


class CustomerUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=200)
    document: str | None = None
    email: EmailStr | None = None
    phone: str | None = Field(default=None, min_length=1, max_length=20)
    address: str | None = Field(default=None, min_length=1, max_length=255)

    @field_validator("document")
    @classmethod
    def validate_document(cls, document: str | None) -> str | None:
        if document is None:
            return None
        return normalize_document(document)

    @model_validator(mode="after")
    def require_update_value(self) -> "CustomerUpdate":
        if not self.model_fields_set:
            raise ValueError("Informe ao menos um campo para atualização")
        if "name" in self.model_fields_set and self.name is None:
            raise ValueError("Nome não pode ser nulo")
        if "document" in self.model_fields_set and self.document is None:
            raise ValueError("Documento não pode ser nulo")
        return self


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    document: str
    email: str | None
    phone: str | None
    address: str | None
    created_at: datetime
    updated_at: datetime
