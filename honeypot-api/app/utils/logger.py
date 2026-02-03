"""
Logging configuration for AI Honeypot API.
"""

import logging
import sys
from app.core.config import settings


def setup_logging() -> None:
    """Configure application logging."""
    
    # Determine log level
    log_level = logging.DEBUG if settings.DEBUG else getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Suppress verbose third-party logs
    logging.getLogger("groq").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured at {settings.LOG_LEVEL} level")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)
