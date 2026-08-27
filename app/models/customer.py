from datetime import datetime, timezone

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.base import AuditMixin


class Customer(AuditMixin, Base):
    __tablename__ = "customers"

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    document: Mapped[str] = mapped_column(
        String(14),
        nullable=False,
        unique=True,
        index=True,
    )
    email: Mapped[str | None] = mapped_column(
        String(320),
        nullable=True,
        default=None,
    )
    phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        default=None,
    )
    address: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        default=None,
    )

    def update_details(
        self,
        *,
        name: str | None = None,
        document: str | None = None,
        email: str | None = None,
        email_provided: bool = False,
        phone: str | None = None,
        phone_provided: bool = False,
        address: str | None = None,
        address_provided: bool = False,
    ) -> None:
        if name is not None:
            self.name = name
        if document is not None:
            self.document = document
        if email_provided:
            self.email = email
        if phone_provided:
            self.phone = phone
        if address_provided:
            self.address = address

    def soft_delete(self) -> None:
        self.deleted_at = datetime.now(timezone.utc)
