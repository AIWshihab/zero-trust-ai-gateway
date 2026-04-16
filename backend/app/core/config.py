import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import field_validator
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
    CORS_ALLOW_ORIGINS: list[str] = ["http://localhost:3000"]

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

    # Database — asyncpg for runtime, override in .env
    DATABASE_URL: str = os.getenv("DATABASE_URL")

    # OpenAI (optional)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    HF_TOKEN: str = os.getenv("HF_TOKEN")

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


@lru_cache
def get_settings() -> Settings:
    return Settings()


# Module-level alias — allows both import styles:
#   from app.core.config import settings       ← used by database.py, etc.
#   from app.core.config import get_settings   ← used as FastAPI Depends()
settings = get_settings()
