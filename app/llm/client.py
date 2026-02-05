"""
LLM Client for AI Honeypot API.
Direct implementation for better modularity and control.
"""

import logging
from typing import Optional, Dict, Any

from app.core.llm import GroqClient as BaseGroqClient

logger = logging.getLogger(__name__)


class GroqClient(BaseGroqClient):
    """
    Enhanced LLM client for Honeypot.
    Inherits base functionality and adds honeymoon-specific orchestration if needed.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key=api_key)
        logger.info("Initialized Enhanced GroqClient")

    async def generate_response(self, prompt: str, **kwargs) -> str:
        """Helper for standard response generation."""
        return await self.generate(prompt, **kwargs)
