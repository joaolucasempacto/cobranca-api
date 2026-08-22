from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from app.core.jwt import create_access_token, create_refresh_token, decode_token
from app.core.security import verify_password
from app.exceptions.base import UnauthorizedError
from app.models.enums import TokenType
from app.models.revoked_token import RevokedToken
from app.models.user import User
from app.repositories.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str


class AuthService:
    def __init__(
        self,
        uow: UnitOfWork,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 15,
        refresh_token_expire_days: int = 7,
    ) -> None:
        self._uow = uow
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._access_token_expire_minutes = access_token_expire_minutes
        self._refresh_token_expire_days = refresh_token_expire_days

    def authenticate(self, email: str, password: str) -> TokenPair:
        user = self._uow.users.get_active_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise UnauthorizedError("Credenciais inválidas")
        return self._create_token_pair(str(user.id))

    def authenticate_access_token(self, access_token: str) -> User:
        payload = decode_token(
            token=access_token,
            secret_key=self._secret_key,
            algorithm=self._algorithm,
            expected_type="access",
        )
        jti = payload.get("jti")
        subject = payload.get("sub")
        if not isinstance(jti, str) or not isinstance(subject, str):
            raise UnauthorizedError("Token inválido ou expirado")
        if self._uow.revoked_tokens.exists_by_jti(jti):
            raise UnauthorizedError("Token revogado")
        try:
            user_id = UUID(subject)
        except ValueError as exc:
            raise UnauthorizedError("Token inválido ou expirado") from exc
        user = self._uow.users.get_active_by_id(user_id)
        if user is None:
            raise UnauthorizedError("Usuário inativo ou não encontrado")
        return user

    def refresh(self, refresh_token: str) -> TokenPair:
        payload = decode_token(
            token=refresh_token,
            secret_key=self._secret_key,
            algorithm=self._algorithm,
            expected_type="refresh",
        )
        jti = payload.get("jti")
        subject = payload.get("sub")
        if not isinstance(jti, str) or not isinstance(subject, str):
            raise UnauthorizedError("Token inválido ou expirado")
        if self._uow.revoked_tokens.exists_by_jti(jti):
            raise UnauthorizedError("Token revogado")
        try:
            user_id = UUID(subject)
        except ValueError as exc:
            raise UnauthorizedError("Token inválido ou expirado") from exc
        user = self._uow.users.get_active_by_id(user_id)
        if user is None:
            raise UnauthorizedError("Usuário inativo ou não encontrado")
        return self._create_token_pair(str(user.id))

    def logout(self, token: str) -> None:
        payload = decode_token(
            token=token,
            secret_key=self._secret_key,
            algorithm=self._algorithm,
        )
        jti = payload.get("jti")
        subject = payload.get("sub")
        token_type = payload.get("type")
        expires_at = payload.get("exp")
        if (
            not isinstance(jti, str)
            or not isinstance(subject, str)
            or token_type not in ("access", "refresh")
            or type(expires_at) not in (int, float)
        ):
            raise UnauthorizedError("Token inválido ou expirado")
        if self._uow.revoked_tokens.exists_by_jti(jti):
            return
        try:
            user_id = UUID(subject)
        except ValueError as exc:
            raise UnauthorizedError("Token inválido ou expirado") from exc
        revoked_token = RevokedToken(
            jti=jti,
            user_id=user_id,
            token_type=TokenType(token_type),
            expires_at=datetime.fromtimestamp(expires_at, tz=timezone.utc),
        )
        self._uow.revoked_tokens.add(revoked_token)
        self._uow.commit()

    def _create_token_pair(self, subject: str) -> TokenPair:
        access_token = create_access_token(
            subject=subject,
            secret_key=self._secret_key,
            algorithm=self._algorithm,
            expires_minutes=self._access_token_expire_minutes,
        )
        refresh_token = create_refresh_token(
            subject=subject,
            secret_key=self._secret_key,
            algorithm=self._algorithm,
            expires_days=self._refresh_token_expire_days,
        )
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
        )
