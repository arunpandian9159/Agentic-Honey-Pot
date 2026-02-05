"""
API Middleware for AI Honeypot API.

Handles cross-cutting concerns like authentication, rate limiting, logging, and error handling.
"""

import time
import logging
from typing import Optional, Callable, Awaitable
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import settings
from app.utils.rate_limiter import rate_limiter

logger = logging.getLogger(__name__)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware for API key authentication."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check API key for protected endpoints."""
        # Skip authentication for health and docs endpoints
        path = request.url.path
        if any(skip in path for skip in ["/health", "/docs", "/openapi.json", "/static"]):
            return await call_next(request)
        
        # Check API key
        api_key = request.headers.get("x-api-key")
        if not api_key:
            logger.warning(f"Missing API key for {request.method} {path}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "Missing API key", "code": "MISSING_API_KEY"}
            )
        
        if api_key != settings.API_SECRET_KEY:
            logger.warning(f"Invalid API key for {request.method} {path}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "Invalid API key", "code": "INVALID_API_KEY"}
            )
        
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting to API requests."""
        # Skip rate limiting for health and docs endpoints
        path = request.url.path
        if any(skip in path for skip in ["/health", "/docs", "/openapi.json", "/static"]):
            return await call_next(request)
        
        # Get client identifier (API key or IP address)
        client_id = request.headers.get("x-api-key") or request.client.host
        
        # Check rate limit
        is_allowed, limit_info = await rate_limiter.check_rate_limit(client_id)
        
        if not is_allowed:
            logger.warning(f"Rate limit exceeded for client {client_id}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "code": "RATE_LIMIT_EXCEEDED",
                    "retry_after": limit_info.get("retry_after", 60)
                },
                headers={
                    "Retry-After": str(limit_info.get("retry_after", 60)),
                    "X-RateLimit-Limit": str(limit_info.get("limit", 0)),
                    "X-RateLimit-Remaining": str(limit_info.get("remaining", 0)),
                    "X-RateLimit-Reset": str(limit_info.get("reset_time", 0))
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(limit_info.get("limit", 0))
        response.headers["X-RateLimit-Remaining"] = str(limit_info.get("remaining", 0))
        response.headers["X-RateLimit-Reset"] = str(limit_info.get("reset_time", 0))
        
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response details."""
        start_time = time.time()
        
        # Log request
        logger.info(f"Incoming request: {request.method} {request.url.path}")
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"Request completed: {request.method} {request.url.path} "
                f"- Status: {response.status_code} - Time: {process_time:.3f}s"
            )
            
            # Add processing time header
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"- Error: {str(e)} - Time: {process_time:.3f}s",
                exc_info=True
            )
            raise


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for global error handling."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle errors globally."""
        try:
            return await call_next(request)
        except HTTPException as e:
            # Handle FastAPI HTTP exceptions
            logger.error(f"HTTP exception: {e.detail}")
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": e.detail,
                    "code": f"HTTP_{e.status_code}",
                    "path": request.url.path
                }
            )
        except Exception as e:
            # Handle unexpected errors
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal server error",
                    "code": "INTERNAL_ERROR",
                    "path": request.url.path,
                    "request_id": getattr(request.state, "request_id", "unknown")
                }
            )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for security headers."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to responses."""
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response