"""
LLM Prompt templates package.
"""

from app.llm.prompts.conversation import CONVERSATION_SYSTEM_PROMPT
from app.llm.prompts.detection import DETECTION_SYSTEM_PROMPT
from app.llm.prompts.extraction import EXTRACTION_SYSTEM_PROMPT

__all__ = [
    "CONVERSATION_SYSTEM_PROMPT",
    "DETECTION_SYSTEM_PROMPT",
    "EXTRACTION_SYSTEM_PROMPT"
]
