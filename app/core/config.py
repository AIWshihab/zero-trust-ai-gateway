from pydantic_settings import BaseSettings
from functools import lru_cache

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

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # Trust Score Thresholds
    TRUST_SCORE_BLOCK: float = 0.75      # block request
    TRUST_SCORE_CHALLENGE: float = 0.50  # flag for review

    # Policy Engine Weights
    WEIGHT_MODEL_RISK: float = 0.25
    WEIGHT_DATA_SENSITIVITY: float = 0.20
    WEIGHT_PROMPT_RISK: float = 0.30
    WEIGHT_REQUEST_RATE: float = 0.15
    WEIGHT_USER_TRUST_PENALTY: float = 0.10

    # Database
    DATABASE_URL: str = "sqlite:///./monitoring/log_store.db"

    # OpenAI (optional)
    OPENAI_API_KEY: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()
