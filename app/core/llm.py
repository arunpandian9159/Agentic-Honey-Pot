"""
Groq LLM client wrapper for AI Honeypot API.
Handles all interactions with Groq's Llama model with rate limiting.

Rate Limits for llama-3.3-70b-versatile:
- RPM: 30 (requests per minute)
- RPD: 1K (requests per day)
- TPM: 12K (tokens per minute)
- TPD: 100K (tokens per day)
"""

import logging
from typing import Optional
from groq import AsyncGroq

from app.core.config import settings
from app.utils.rate_limiter import rate_limiter

logger = logging.getLogger(__name__)


class GroqClient:
    """Wrapper for Groq API client with rate limiting and request tracking."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.client = AsyncGroq(api_key=self.api_key)
        self.model = settings.LLM_MODEL
        self.request_count = 0
        self.total_tokens = 0
    
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 150,  # Reduced from 500 to save tokens
        response_format: Optional[str] = None
    ) -> str:
        """
        Generate a response from Groq LLM with rate limiting.
        
        Args:
            prompt: The prompt to send to the LLM
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response (reduced to 150 for efficiency)
            response_format: Optional format ("json" for JSON mode)
        
        Returns:
            Generated text response
        """
        try:
            # Estimate tokens (rough: 1 token ≈ 4 chars)
            estimated_tokens = len(prompt) // 4 + max_tokens
            
            # Wait if rate limits would be exceeded
            wait_time = await rate_limiter.wait_if_needed(estimated_tokens)
            if wait_time:
                logger.info(f"Rate limit wait: {wait_time:.1f}s")
            
            self.request_count += 1
            
            # Prepare request parameters
            params = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            # Add JSON mode if requested
            if response_format == "json":
                params["response_format"] = {"type": "json_object"}
            
            # Make API call
            response = await self.client.chat.completions.create(**params)
            
            # Extract content and track tokens
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            self.total_tokens += tokens_used
            
            # Record in rate limiter
            rate_limiter.record_request(tokens_used)
            
            # Log usage stats
            usage = rate_limiter.get_current_usage()
            logger.info(
                f"Request #{self.request_count}: {tokens_used} tokens | "
                f"RPM: {usage['requests_this_minute']}/30 | "
                f"RPD: {usage['requests_today']}/1000 | "
                f"TPM: {usage['tokens_this_minute']}/12000"
            )
            
            return content.strip()
            
        except Exception as e:
            logger.error(f"Groq API error: {str(e)}")
            raise
    
    async def generate_json(
        self,
        prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 200  # Reduced for JSON responses
    ) -> str:
        """
        Generate a JSON response specifically.
        Uses low temperature for consistency.
        
        Args:
            prompt: The prompt expecting JSON output
            temperature: Sampling temperature (default 0.1 for consistency)
            max_tokens: Maximum tokens (reduced to 200 for JSON)
        
        Returns:
            JSON string response
        """
        return await self.generate(
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format="json"
        )
    
    def get_request_count(self) -> int:
        """Get the total number of requests made."""
        return self.request_count
    
    def get_total_tokens(self) -> int:
        """Get total tokens used."""
        return self.total_tokens
    
    def get_usage_stats(self) -> dict:
        """Get current usage statistics."""
        usage = rate_limiter.get_current_usage()
        usage["total_requests"] = self.request_count
        usage["total_tokens_all_time"] = self.total_tokens
        return usage
