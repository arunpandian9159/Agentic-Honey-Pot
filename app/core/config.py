"""
Configuration management for AI Honeypot API.
Loads settings from environment variables via pydantic-settings.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Required
    GROQ_API_KEY: str = ""
    API_SECRET_KEY: str = ""
    GUVI_CALLBACK_URL: str = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

    # Optional with defaults
    PORT: int = 8000
    ENVIRONMENT: str = "production"
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False
    EXTRACTION_ENABLED: bool = True
    EARLY_STAGE_LIMIT: int = 3
    MID_STAGE_LIMIT: int = 6
    TACTIC_COOLDOWN_MESSAGES: int = 3

    # Session settings
    SESSION_TIMEOUT_MINUTES: int = 30
    MAX_MESSAGES_PER_SESSION: int = 18
    INTELLIGENCE_SCORE_THRESHOLD: float = 6.0

    # LLM settings
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    SCAM_DETECTION_THRESHOLD: float = 0.65
    MAX_TOKENS_GENERATION: int = 300
    MAX_TOKENS_JSON: int = 200

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
