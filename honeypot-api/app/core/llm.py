"""
Groq LLM client wrapper for AI Honeypot API.
Handles all interactions with Groq's Llama model.
"""

import logging
from typing import Optional
from groq import AsyncGroq

from app.core.config import settings

logger = logging.getLogger(__name__)


class GroqClient:
    """Wrapper for Groq API client with request tracking."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.client = AsyncGroq(api_key=self.api_key)
        self.model = settings.LLM_MODEL
        self.request_count = 0
    
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 500,
        response_format: Optional[str] = None
    ) -> str:
        """
        Generate a response from Groq LLM.
        
        Args:
            prompt: The prompt to send to the LLM
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response
            response_format: Optional format ("json" for JSON mode)
        
        Returns:
            Generated text response
        """
        try:
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
            
            # Extract content
            content = response.choices[0].message.content
            
            logger.info(
                f"Groq request #{self.request_count} completed. "
                f"Tokens: {response.usage.total_tokens}"
            )
            
            return content.strip()
            
        except Exception as e:
            logger.error(f"Groq API error: {str(e)}")
            raise
    
    async def generate_json(
        self,
        prompt: str,
        temperature: float = 0.1
    ) -> str:
        """
        Generate a JSON response specifically.
        Uses low temperature for consistency.
        
        Args:
            prompt: The prompt expecting JSON output
            temperature: Sampling temperature (default 0.1 for consistency)
        
        Returns:
            JSON string response
        """
        return await self.generate(
            prompt=prompt,
            temperature=temperature,
            response_format="json"
        )
    
    def get_request_count(self) -> int:
        """Get the total number of requests made."""
        return self.request_count
