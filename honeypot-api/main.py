"""
AI Honeypot API - Main Application Entry Point

An AI-powered honeypot system that autonomously detects scam messages,
engages scammers with convincing human-like personas, and extracts
actionable intelligence.
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging before importing other modules
from app.utils.logger import setup_logging
setup_logging()

from app.core.config import settings
from app.api.routes import router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("=" * 50)
    logger.info("AI Honeypot API Starting...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug Mode: {settings.DEBUG}")
    logger.info(f"Log Level: {settings.LOG_LEVEL}")
    
    # Validate required settings
    if not settings.GROQ_API_KEY:
        logger.warning("⚠️ GROQ_API_KEY not set! LLM features will fail.")
    else:
        logger.info("✓ GROQ_API_KEY configured")
    
    if not settings.API_SECRET_KEY:
        logger.warning("⚠️ API_SECRET_KEY not set! API authentication disabled.")
    else:
        logger.info("✓ API_SECRET_KEY configured")
    
    logger.info(f"✓ Callback URL: {settings.GUVI_CALLBACK_URL}")
    logger.info("=" * 50)
    logger.info("🚀 AI Honeypot API Ready!")
    
    yield
    
    # Shutdown
    logger.info("AI Honeypot API Shutting down...")
    logger.info("Goodbye! 👋")


# Create FastAPI application
app = FastAPI(
    title="AI Honeypot API",
    description=(
        "AI-powered honeypot system for scam detection and intelligence extraction. "
        "Detects scam messages, engages scammers with adaptive personas, "
        "and extracts valuable intelligence like bank accounts, UPI IDs, and phishing links."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for hackathon
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return {
        "status": "error",
        "message": "An internal error occurred",
        "detail": str(exc) if settings.DEBUG else None
    }


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
