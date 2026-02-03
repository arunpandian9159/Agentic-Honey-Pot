"""
Rate Limiter for Groq API compliance.
Tracks requests and tokens to stay within free tier limits.
"""

import asyncio
import time
import logging
from typing import Optional
from dataclasses import dataclass, field
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limit configuration for Groq llama-3.3-70b-versatile"""
    requests_per_minute: int = 30
    requests_per_day: int = 1000
    tokens_per_minute: int = 12000
    tokens_per_day: int = 100000


@dataclass
class RateLimiter:
    """
    Token bucket rate limiter for Groq API.
    Tracks both requests and tokens to stay within limits.
    """
    config: RateLimitConfig = field(default_factory=RateLimitConfig)
    
    # Request tracking
    _minute_requests: deque = field(default_factory=deque)
    _day_requests: deque = field(default_factory=deque)
    
    # Token tracking
    _minute_tokens: deque = field(default_factory=deque)
    _day_tokens: deque = field(default_factory=deque)
    
    def __post_init__(self):
        self._minute_requests = deque()
        self._day_requests = deque()
        self._minute_tokens = deque()
        self._day_tokens = deque()
    
    def _cleanup_old_entries(self):
        """Remove expired entries from tracking queues."""
        now = time.time()
        minute_ago = now - 60
        day_ago = now - 86400
        
        # Clean minute queues
        while self._minute_requests and self._minute_requests[0] < minute_ago:
            self._minute_requests.popleft()
        while self._minute_tokens and self._minute_tokens[0][0] < minute_ago:
            self._minute_tokens.popleft()
        
        # Clean day queues
        while self._day_requests and self._day_requests[0] < day_ago:
            self._day_requests.popleft()
        while self._day_tokens and self._day_tokens[0][0] < day_ago:
            self._day_tokens.popleft()
    
    def get_current_usage(self) -> dict:
        """Get current usage statistics."""
        self._cleanup_old_entries()
        
        minute_tokens = sum(t[1] for t in self._minute_tokens)
        day_tokens = sum(t[1] for t in self._day_tokens)
        
        return {
            "requests_this_minute": len(self._minute_requests),
            "requests_today": len(self._day_requests),
            "tokens_this_minute": minute_tokens,
            "tokens_today": day_tokens,
            "rpm_remaining": self.config.requests_per_minute - len(self._minute_requests),
            "rpd_remaining": self.config.requests_per_day - len(self._day_requests),
            "tpm_remaining": self.config.tokens_per_minute - minute_tokens,
            "tpd_remaining": self.config.tokens_per_day - day_tokens,
        }
    
    async def wait_if_needed(self, estimated_tokens: int = 500) -> Optional[float]:
        """
        Wait if rate limits would be exceeded.
        
        Args:
            estimated_tokens: Estimated tokens for the upcoming request
        
        Returns:
            Wait time in seconds, or None if no wait needed
        """
        self._cleanup_old_entries()
        
        now = time.time()
        wait_time = 0.0
        
        # Check RPM limit
        if len(self._minute_requests) >= self.config.requests_per_minute:
            oldest = self._minute_requests[0]
            wait_time = max(wait_time, 60 - (now - oldest) + 0.1)
            logger.warning(f"RPM limit reached, waiting {wait_time:.1f}s")
        
        # Check RPD limit
        if len(self._day_requests) >= self.config.requests_per_day:
            oldest = self._day_requests[0]
            wait_time = max(wait_time, 86400 - (now - oldest) + 0.1)
            logger.error(f"RPD limit reached! Must wait {wait_time:.0f}s")
        
        # Check TPM limit
        minute_tokens = sum(t[1] for t in self._minute_tokens)
        if minute_tokens + estimated_tokens > self.config.tokens_per_minute:
            if self._minute_tokens:
                oldest = self._minute_tokens[0][0]
                wait_time = max(wait_time, 60 - (now - oldest) + 0.1)
                logger.warning(f"TPM limit near, waiting {wait_time:.1f}s")
        
        # Check TPD limit
        day_tokens = sum(t[1] for t in self._day_tokens)
        if day_tokens + estimated_tokens > self.config.tokens_per_day:
            logger.error(f"TPD limit reached! {day_tokens}/{self.config.tokens_per_day}")
            # Don't wait for day limit - just warn
        
        if wait_time > 0:
            await asyncio.sleep(wait_time)
            return wait_time
        
        return None
    
    def record_request(self, tokens_used: int = 0):
        """Record a completed request."""
        now = time.time()
        
        self._minute_requests.append(now)
        self._day_requests.append(now)
        
        if tokens_used > 0:
            self._minute_tokens.append((now, tokens_used))
            self._day_tokens.append((now, tokens_used))
        
        logger.debug(f"Recorded request: {tokens_used} tokens")
    
    def can_make_request(self, estimated_tokens: int = 500) -> bool:
        """Check if a request can be made without exceeding limits."""
        self._cleanup_old_entries()
        
        if len(self._minute_requests) >= self.config.requests_per_minute:
            return False
        if len(self._day_requests) >= self.config.requests_per_day:
            return False
        
        minute_tokens = sum(t[1] for t in self._minute_tokens)
        if minute_tokens + estimated_tokens > self.config.tokens_per_minute:
            return False
        
        day_tokens = sum(t[1] for t in self._day_tokens)
        if day_tokens + estimated_tokens > self.config.tokens_per_day:
            return False
        
        return True


# Global rate limiter instance
rate_limiter = RateLimiter()
