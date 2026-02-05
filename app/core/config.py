"""
Configuration management for AI Honeypot API.
Loads settings from environment variables.
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Required
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    API_SECRET_KEY: str = os.getenv("API_SECRET_KEY", "")
    GUVI_CALLBACK_URL: str = os.getenv(
        "GUVI_CALLBACK_URL", 
        "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"
    )
    
    # Optional with defaults
    PORT: int = int(os.getenv("PORT", "8000"))
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    EXTRACTION_ENABLED: bool = os.getenv("EXTRACTION_ENABLED", "true").lower() == "true"
    EARLY_STAGE_LIMIT: int = int(os.getenv("EARLY_STAGE_LIMIT", "3"))
    MID_STAGE_LIMIT: int = int(os.getenv("MID_STAGE_LIMIT", "6"))
    TACTIC_COOLDOWN_MESSAGES: int = int(os.getenv("TACTIC_COOLDOWN_MESSAGES", "3"))
    
    # Session settings
    SESSION_TIMEOUT_MINUTES: int = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))
    MAX_MESSAGES_PER_SESSION: int = int(os.getenv("MAX_MESSAGES_PER_SESSION", "12"))
    INTELLIGENCE_SCORE_THRESHOLD: float = float(os.getenv("INTELLIGENCE_SCORE_THRESHOLD", "6"))
    
    # LLM settings
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    SCAM_DETECTION_THRESHOLD: float = 0.65
    
    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
