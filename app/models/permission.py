from datetime import datetime, timezone

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.base import AuditMixin


class Permission(AuditMixin, Base):
    __tablename__ = "permissions"

    code: Mapped[str] = mapped_column(
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
        code: str | None = None,
        description: str | None = None,
    ) -> None:
        if code is not None:
            self.code = code
        if description is not None:
            self.description = description

    def soft_delete(self) -> None:
        self.deleted_at = datetime.now(timezone.utc)
