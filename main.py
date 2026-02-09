"""
AI Honeypot API - Main Application Entry Point

An AI-powered honeypot system that autonomously detects scam messages,
engages scammers with convincing human-like personas, and extracts
actionable intelligence.
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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
    RAG is initialized lazily on first request.
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
    
    # Note: RAG is initialized lazily on first request
    # This reduces cold start time by 2-3 minutes
    logger.info("=" * 50)
    logger.info("🚀 AI Honeypot API Ready!")
    logger.info("Frontend is in http://localhost:8000/")
    
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


# Lazy RAG initialization middleware
@app.middleware("http")
async def init_rag_on_first_request(request: Request, call_next):
    """Lazy initialize RAG on first request to reduce startup time."""
    if not hasattr(app.state, 'rag_initialized'):
        from app.core.rag_config import is_rag_enabled, initialize_collections
        if is_rag_enabled():
            if initialize_collections():
                logger.info("✓ RAG system initialized on first request")
            else:
                logger.warning("⚠️ RAG initialization failed, continuing without RAG")
        else:
            logger.info("ℹ️ RAG disabled (QDRANT_URL/QDRANT_API_KEY not set)")
        app.state.rag_initialized = True
    return await call_next(request)


# Include API routes
app.include_router(router)
 
# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/")
async def serve_dashboard():
    """Serve the interactive dashboard."""
    return FileResponse("app/static/index.html")


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
