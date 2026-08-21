from app.exceptions.base import NotFoundError
from app.models.revoked_token import RevokedToken
from app.repositories.unit_of_work import UnitOfWork


class RevokedTokenService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def get_by_jti(self, jti: str) -> RevokedToken:
        revoked_token = self._uow.revoked_tokens.get_by_jti(jti)
        if revoked_token is None:
            raise NotFoundError("Token revogado não encontrado")
        return revoked_token

    def is_revoked(self, jti: str) -> bool:
        return self._uow.revoked_tokens.exists_by_jti(jti)

    def add(self, revoked_token: RevokedToken) -> RevokedToken:
        added_token = self._uow.revoked_tokens.add(revoked_token)
        self._uow.commit()
        return added_token
