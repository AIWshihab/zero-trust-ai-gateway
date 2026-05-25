import os
from functools import lru_cache
from urllib.parse import quote, urlsplit, urlunsplit

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

load_dotenv()


def _coerce_bool_env(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if value is None:
        return value

    normalized = str(value).strip().lower()
    truthy = {"1", "true", "t", "yes", "y", "on", "debug", "development", "dev"}
    falsy = {"0", "false", "f", "no", "n", "off", "release", "prod", "production"}

    if normalized in truthy:
        return True
    if normalized in falsy:
        return False

    raise ValueError(
        f"Invalid boolean-like value: {value!r}. "
        "Use one of true/false/1/0/on/off/debug/release."
    )


def _build_database_url_from_pg_env() -> str | None:
    host = os.getenv("PGHOST")
    user = os.getenv("PGUSER")
    password = os.getenv("PGPASSWORD")
    database = os.getenv("PGDATABASE")
    port = os.getenv("PGPORT") or "5432"

    if not all((host, user, password, database)):
        return None

    return (
        "postgresql+asyncpg://"
        f"{quote(user, safe='')}:{quote(password, safe='')}"
        f"@{host}:{port}/{quote(database, safe='')}"
    )


def _database_url_from_env() -> str | None:
    return (
        os.getenv("DATABASE_URL")
        or os.getenv("DATABASE_PRIVATE_URL")
        or os.getenv("DATABASE_PUBLIC_URL")
        or _build_database_url_from_pg_env()
    )


def _normalize_database_url(value: str | None) -> str:
    raw = (value or "").strip()
    if not raw:
        if _requires_external_database():
            raise ValueError(
                "No PostgreSQL connection was configured. Set DATABASE_URL on the "
                "Railway app service to the Postgres service reference, for example "
                "${{Postgres.DATABASE_URL}}."
            )
        return "sqlite+aiosqlite:///./dev.db"

    if raw.startswith("postgres://"):
        raw = "postgresql+asyncpg://" + raw.removeprefix("postgres://")
    elif raw.startswith("postgresql://"):
        raw = "postgresql+asyncpg://" + raw.removeprefix("postgresql://")

    if raw.startswith("postgresql+asyncpg://"):
        parts = urlsplit(raw)
        if parts.netloc.endswith(":"):
            port = os.getenv("PGPORT") or "5432"
            raw = urlunsplit(
                (
                    parts.scheme,
                    f"{parts.netloc}{port}",
                    parts.path,
                    parts.query,
                    parts.fragment,
                )
            )

    return raw


def resolve_database_url(value: str | None = None) -> str:
    return _normalize_database_url(value or _database_url_from_env())


def _requires_external_database() -> bool:
    value = os.getenv("REQUIRE_EXTERNAL_DATABASE")
    if value is not None:
        return _coerce_bool_env(value)
    return bool(os.getenv("RAILWAY_ENVIRONMENT_ID") or os.getenv("RAILWAY_SERVICE_ID"))


def database_dialect(database_url: str) -> str:
    scheme = urlsplit(database_url).scheme
    return scheme.split("+", 1)[0] or "unknown"


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Zero Trust AI Gateway"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    ZTA_ENABLED: bool = True
    MODEL_RISK_ENABLED: bool = True
    PROMPT_ANALYSIS_ENABLED: bool = True
    RATE_LIMITING_ENABLED: bool = True
    USER_TRUST_SCORE_ENABLED: bool = True
    CORS_ALLOW_ORIGINS: list[str] = Field(
        default_factory=lambda: (
            os.getenv("BACKEND_CORS_ORIGINS", "").split(",")
            if os.getenv("BACKEND_CORS_ORIGINS")
            else ["http://localhost:3000"]
        )
    )

    # Startup DB behavior
    # Keep this False in normal development and production.
    # Rely on Alembic migrations instead of implicit table creation.
    AUTO_INIT_SCHEMA: bool = False

    # JWT
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # Trust Score Thresholds
    TRUST_SCORE_BLOCK: float = 0.75
    TRUST_SCORE_CHALLENGE: float = 0.50

    # Policy Engine Weights
    WEIGHT_MODEL_RISK: float = 0.25
    WEIGHT_DATA_SENSITIVITY: float = 0.20
    WEIGHT_PROMPT_RISK: float = 0.30
    WEIGHT_REQUEST_RATE: float = 0.15
    WEIGHT_USER_TRUST_PENALTY: float = 0.10

    # Database: set DATABASE_URL in production. SQLite is only a local fallback.
    DATABASE_URL: str = Field(default_factory=resolve_database_url)

    # OpenAI (optional)
    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
    HF_TOKEN: str | None = os.getenv("HF_TOKEN")
    GATEWAY_API_KEYS: str | None = os.getenv("GATEWAY_API_KEYS")
    DEFAULT_GATEWAY_API_KEY: str | None = os.getenv("DEFAULT_GATEWAY_API_KEY")

    # Production deployment settings
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    FRONTEND_ORIGIN: str | None = os.getenv("FRONTEND_ORIGIN")
    BROWSER_EXTENSION_ORIGIN_REGEX: str | None = os.getenv(
        "BROWSER_EXTENSION_ORIGIN_REGEX",
        r"^chrome-extension://[a-z]{32}$",
    )
    CHROME_EXTENSION_STORE_URL: str | None = os.getenv("CHROME_EXTENSION_STORE_URL")
    EXTENSION_ID: str | None = os.getenv("EXTENSION_ID")
    PUBLIC_GATEWAY_API_URL: str | None = os.getenv("PUBLIC_GATEWAY_API_URL")
    SECURE_COOKIES: bool = Field(
        default_factory=lambda: _coerce_bool_env(os.getenv("SECURE_COOKIES", "false"))
    )
    TRUST_PROXY_HEADERS: bool = Field(
        default_factory=lambda: _coerce_bool_env(os.getenv("TRUST_PROXY_HEADERS", "false"))
    )

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore",
    }

    @field_validator(
        "DEBUG",
        "ZTA_ENABLED",
        "MODEL_RISK_ENABLED",
        "PROMPT_ANALYSIS_ENABLED",
        "RATE_LIMITING_ENABLED",
        "USER_TRUST_SCORE_ENABLED",
        "AUTO_INIT_SCHEMA",
        mode="before",
    )
    @classmethod
    def _parse_loose_bool(cls, value):
        return _coerce_bool_env(value)

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def _parse_database_url(cls, value):
        if not str(value or "").strip():
            return resolve_database_url()
        return resolve_database_url(str(value))

    @property
    def DATABASE_DIALECT(self) -> str:
        return database_dialect(self.DATABASE_URL)


@lru_cache
def get_settings() -> Settings:
    return Settings()


# Module-level alias — allows both import styles:
#   from app.core.config import settings       ← used by database.py, etc.
#   from app.core.config import get_settings   ← used as FastAPI Depends()
settings = get_settings()
