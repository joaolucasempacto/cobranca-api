from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


JWT_SECRET_PLACEHOLDER = "change-this-to-a-long-random-secret"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    PROJECT_NAME: str = "cobranca-api"
    ENVIRONMENT: str = "development"

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int

    DATABASE_URL: str

    JWT_SECRET_KEY: str = Field(min_length=32)
    JWT_ALGORITHM: Literal["HS256"] = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, gt=0)
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, gt=0)

    @model_validator(mode="after")
    def reject_production_placeholder_secret(self) -> "Settings":
        if (
            self.ENVIRONMENT.lower() in {"production", "prod"}
            and self.JWT_SECRET_KEY == JWT_SECRET_PLACEHOLDER
        ):
            raise ValueError(
                "JWT_SECRET_KEY padrão não pode ser usado em produção"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
