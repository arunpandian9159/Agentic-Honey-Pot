"""
Security utilities for AI Honeypot API.

Handles API key validation and security-related functionality.
"""

import secrets
import hashlib
import hmac
from typing import Optional
from fastapi import HTTPException, Header, status

from app.core.config import settings
from app.core.exceptions import AuthenticationError, AuthorizationError


def validate_api_key(api_key: str) -> bool:
    """
    Validate API key against configured secret.
    
    Args:
        api_key: API key to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not api_key or not settings.API_SECRET_KEY:
        return False
    
    # Use constant-time comparison to prevent timing attacks
    return secrets.compare_digest(api_key, settings.API_SECRET_KEY)


def generate_api_key() -> str:
    """
    Generate a secure API key.
    
    Returns:
        Generated API key
    """
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key for storage.
    
    Args:
        api_key: API key to hash
        
    Returns:
        Hashed API key
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key_header(x_api_key: Optional[str] = Header(None, alias="x-api-key")) -> str:
    """
    Verify API key from request header.
    
    Args:
        x_api_key: API key from header
        
    Returns:
        Validated API key
        
    Raises:
        HTTPException: If API key is invalid or missing
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    if not validate_api_key(x_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    return x_api_key


class RateLimiter:
    """Simple rate limiter for API requests."""
    
    def __init__(self, requests_per_minute: int = 60, requests_per_day: int = 1000):
        self.requests_per_minute = requests_per_minute
        self.requests_per_day = requests_per_day
        self._request_counts = {}
    
    def is_allowed(self, client_id: str) -> tuple[bool, dict]:
        """
        Check if request is allowed for client.
        
        Args:
            client_id: Client identifier
            
        Returns:
            Tuple of (is_allowed, limit_info)
        """
        # Simple implementation - in production, use Redis or similar
        import time
        
        current_time = time.time()
        
        # Clean old entries
        self._cleanup_old_entries(current_time)
        
        # Get client data
        client_data = self._request_counts.get(client_id, {
            "minute_requests": [],
            "day_requests": [],
            "blocked_until": 0
        })
        
        # Check if blocked
        if client_data["blocked_until"] > current_time:
            return False, {
                "retry_after": int(client_data["blocked_until"] - current_time),
                "limit": self.requests_per_minute,
                "remaining": 0
            }
        
        # Check minute limit
        recent_minute_requests = [
            req_time for req_time in client_data["minute_requests"]
            if current_time - req_time < 60
        ]
        
        if len(recent_minute_requests) >= self.requests_per_minute:
            # Block for 1 minute
            client_data["blocked_until"] = current_time + 60
            self._request_counts[client_id] = client_data
            return False, {
                "retry_after": 60,
                "limit": self.requests_per_minute,
                "remaining": 0
            }
        
        # Check day limit
        recent_day_requests = [
            req_time for req_time in client_data["day_requests"]
            if current_time - req_time < 86400  # 24 hours
        ]
        
        if len(recent_day_requests) >= self.requests_per_day:
            # Block for 24 hours
            client_data["blocked_until"] = current_time + 86400
            self._request_counts[client_id] = client_data
            return False, {
                "retry_after": 86400,
                "limit": self.requests_per_day,
                "remaining": 0
            }
        
        # Record request
        client_data["minute_requests"].append(current_time)
        client_data["day_requests"].append(current_time)
        self._request_counts[client_id] = client_data
        
        return True, {
            "limit": self.requests_per_minute,
            "remaining": self.requests_per_minute - len(recent_minute_requests) - 1
        }
    
    def _cleanup_old_entries(self, current_time: float) -> None:
        """Clean up old request entries."""
        cutoff_time = current_time - 86400  # 24 hours
        
        clients_to_remove = []
        for client_id, client_data in self._request_counts.items():
            # Clean minute requests
            client_data["minute_requests"] = [
                req_time for req_time in client_data["minute_requests"]
                if current_time - req_time < 60
            ]
            
            # Clean day requests
            client_data["day_requests"] = [
                req_time for req_time in client_data["day_requests"]
                if current_time - req_time < 86400
            ]
            
            # Remove if no recent requests and not blocked
            if (not client_data["minute_requests"] and 
                not client_data["day_requests"] and 
                client_data["blocked_until"] < current_time):
                clients_to_remove.append(client_id)
            else:
                self._request_counts[client_id] = client_data
        
        # Remove old clients
        for client_id in clients_to_remove:
            del self._request_counts[client_id]


# Global rate limiter instance
_rate_limiter = RateLimiter(
    requests_per_minute=settings.RATE_LIMIT_PER_MINUTE or 30,
    requests_per_day=settings.RATE_LIMIT_PER_DAY or 1000
)


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance."""
    return _rate_limiter
