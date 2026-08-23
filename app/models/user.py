from datetime import datetime, timezone

from sqlalchemy import Boolean, String, true
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.base import AuditMixin


class User(AuditMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
        unique=True,
        index=True,
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=true(),
    )

    def update_details(
        self,
        *,
        email: str | None = None,
        password_hash: str | None = None,
        is_active: bool | None = None,
    ) -> None:
        if email is not None:
            self.email = email
        if password_hash is not None:
            self.password_hash = password_hash
        if is_active is not None:
            self.is_active = is_active

    def soft_delete(self) -> None:
        self.is_active = False
        self.deleted_at = datetime.now(timezone.utc)
