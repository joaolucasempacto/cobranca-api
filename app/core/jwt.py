from datetime import datetime, timedelta, timezone
from typing import Any, Literal
from uuid import uuid4

import jwt
from jwt import InvalidTokenError

from app.exceptions.base import UnauthorizedError

TokenType = Literal["access", "refresh"]


def _create_token(
    subject: str,
    token_type: TokenType,
    secret_key: str,
    algorithm: str,
    expires_delta: timedelta,
) -> str:
    if not subject:
        raise ValueError("JWT subject must not be empty")

    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "jti": str(uuid4()),
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, secret_key, algorithm=algorithm)


def create_access_token(
    subject: str,
    secret_key: str,
    algorithm: str = "HS256",
    expires_minutes: int = 15,
) -> str:
    return _create_token(
        subject=subject,
        token_type="access",
        secret_key=secret_key,
        algorithm=algorithm,
        expires_delta=timedelta(minutes=expires_minutes),
    )


def create_refresh_token(
    subject: str,
    secret_key: str,
    algorithm: str = "HS256",
    expires_days: int = 7,
) -> str:
    return _create_token(
        subject=subject,
        token_type="refresh",
        secret_key=secret_key,
        algorithm=algorithm,
        expires_delta=timedelta(days=expires_days),
    )


def decode_token(
    token: str,
    secret_key: str,
    algorithm: str = "HS256",
    expected_type: TokenType | None = None,
) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=[algorithm],
            options={"require": ["sub", "type", "jti", "iat", "exp"]},
        )
    except InvalidTokenError as exc:
        raise UnauthorizedError("Token inválido ou expirado") from exc

    subject = payload.get("sub")
    jti = payload.get("jti")
    issued_at = payload.get("iat")
    expires_at = payload.get("exp")
    if (
        not isinstance(subject, str)
        or not subject
        or not isinstance(jti, str)
        or not jti
        or type(issued_at) not in (int, float)
        or type(expires_at) not in (int, float)
    ):
        raise UnauthorizedError("Token inválido ou expirado")

    token_type = payload.get("type")
    if token_type not in ("access", "refresh"):
        raise UnauthorizedError("Tipo de token inválido")
    if expected_type is not None and token_type != expected_type:
        raise UnauthorizedError("Tipo de token inesperado")

    return payload
