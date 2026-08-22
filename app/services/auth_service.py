from dataclasses import dataclass

from app.core.jwt import create_access_token, create_refresh_token
from app.core.security import verify_password
from app.exceptions.base import UnauthorizedError
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

        subject = str(user.id)
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
