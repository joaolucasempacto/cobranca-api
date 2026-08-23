from datetime import datetime, timezone

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.base import AuditMixin


class Role(AuditMixin, Base):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        default=None,
    )

    def update_details(
        self,
        name: str | None = None,
        description: str | None = None,
        description_provided: bool = False,
    ) -> None:
        if name is not None:
            self.name = name
        if description_provided:
            self.description = description

    def soft_delete(self) -> None:
        self.deleted_at = datetime.now(timezone.utc)
