"""Application settings loaded from environment variables / ``.env``.

Uses :mod:`pydantic_settings` (v2). Three tiers are provided:

* ``DevelopmentSettings`` — local defaults, verbose logging, hot reload.
* ``TestingSettings`` — isolated test database, low timeouts.
* ``ProductionSettings`` — strict, secret-driven, no debug.

The active class is chosen via the ``APP_ENV`` environment variable
(``development`` | ``testing`` | ``production``). All secrets are read
from the environment so the codebase contains zero credentials.
"""

from __future__ import annotations

from datetime import timedelta
from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# The database/redis URLs default to the docker-compose service names so
# that `docker compose up --build` works with zero configuration.
_DEFAULT_DATABASE_URL = "postgresql+psycopg2://wealth:wealth@localhost:5432/wealth_db"
_DEFAULT_TEST_DATABASE_URL = "postgresql+psycopg2://wealth:wealth@localhost:5432/wealth_test"
_DEFAULT_REDIS_URL = "redis://localhost:6379/0"


class BaseAppSettings(BaseSettings):
    """Common settings shared by every environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── app ─────────────────────────────────────────────────────────
    APP_NAME: str = "Wealth Management System API"
    APP_VERSION: str = "1.0.0"
    APP_ENV: Literal["development", "testing", "production"] = "development"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    # Comma-separated list of allowed CORS origins.
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # ── security ────────────────────────────────────────────────────
    SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    EMAIL_VERIFICATION_EXPIRE_HOURS: int = 24
    PASSWORD_RESET_EXPIRE_HOURS: int = 1
    BCRYPT_ROUNDS: int = 12

    # ── database ────────────────────────────────────────────────────
    DATABASE_URL: str = _DEFAULT_DATABASE_URL
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # ── redis ───────────────────────────────────────────────────────
    REDIS_URL: str = _DEFAULT_REDIS_URL
    REDIS_SESSION_TTL_SECONDS: int = 60 * 60 * 24

    # ── rate limiting ───────────────────────────────────────────────
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT: str = "60/minute"
    RATE_LIMIT_AUTH: str = "10/minute"

    # ── logging ─────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = False

    # ── background tasks ────────────────────────────────────────────
    SCHEDULER_ENABLED: bool = True
    MARKET_DATA_REFRESH_HOURS: int = 6
    SNAPSHOT_GENERATION_HOURS: int = 24

    # ── derived properties ──────────────────────────────────────────

    @property
    def refresh_token_expire_seconds(self) -> int:
        """Seconds until a refresh token expires (auth service shorthand)."""
        return self.REFRESH_TOKEN_EXPIRE_MINUTES * 60

    @property
    def access_token_expire_seconds(self) -> int:
        """Seconds until an access token expires."""
        return self.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    @property
    def jwt_expiry(self) -> timedelta:
        """Alias used by token blacklisting (access token lifetime)."""
        return timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _split_cors_origins(cls, value: object) -> object:
        """Accept either a JSON list or a comma-separated string."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


class DevelopmentSettings(BaseAppSettings):
    """Local development — verbose, hot-reload, SQL echo on."""

    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    DB_ECHO: bool = True
    LOG_JSON: bool = False


class TestingSettings(BaseAppSettings):
    """Automated tests — isolated DB, deterministic, no external deps."""

    APP_ENV: Literal["development", "testing", "production"] = "testing"
    DEBUG: bool = False
    DATABASE_URL: str = _DEFAULT_TEST_DATABASE_URL
    RATE_LIMIT_ENABLED: bool = False
    SCHEDULER_ENABLED: bool = False
    LOG_JSON: bool = False


class ProductionSettings(BaseAppSettings):
    """Production — strict validation, JSON logs, no debug."""

    APP_ENV: Literal["development", "testing", "production"] = "production"
    DEBUG: bool = False
    LOG_JSON: bool = True

    @field_validator("SECRET_KEY")
    @classmethod
    def _secret_key_must_be_strong(cls, value: str) -> str:
        if value == "change-me-in-production" or len(value) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters and overridden in production"
            )
        return value


_ENV_CLASSES = {
    "development": DevelopmentSettings,
    "testing": TestingSettings,
    "production": ProductionSettings,
}


@lru_cache
def get_settings() -> BaseAppSettings:
    """Return the process-wide cached settings instance.

    Cached so the whole application agrees on one configuration object
    for its lifetime (mirrors the engine's ``get_config`` pattern).
    """
    import os

    env = os.getenv("APP_ENV", "development")
    cls = _ENV_CLASSES.get(env, DevelopmentSettings)
    return cls()


settings = get_settings()

