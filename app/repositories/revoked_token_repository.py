from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.revoked_token import RevokedToken


class RevokedTokenRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_jti(self, jti: str) -> RevokedToken | None:
        statement = select(RevokedToken).where(
            RevokedToken.jti == jti,
            RevokedToken.deleted_at.is_(None),
        )
        return self._session.scalar(statement)

    def exists_by_jti(self, jti: str) -> bool:
        statement = select(RevokedToken.id).where(
            RevokedToken.jti == jti,
            RevokedToken.deleted_at.is_(None),
        )
        return self._session.scalar(statement) is not None

    def add(self, revoked_token: RevokedToken) -> RevokedToken:
        self._session.add(revoked_token)
        self._session.flush()
        return revoked_token
