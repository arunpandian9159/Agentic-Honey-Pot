"""
Response parsing utilities for LLM outputs.
"""

import json
import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def extract_json(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract JSON object from LLM response text.
    Handles markdown blocks and loose JSON.
    """
    try:
        # Try to find JSON block in markdown
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
            
        # Try to find the first '{' and last '}'
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            return json.loads(text[start:end+1])
            
        # Try direct load
        return json.loads(text)
    except Exception as e:
        logger.error(f"Failed to extract JSON from LLM output: {e}")
        return None


def parse_llm_result(text: str) -> str:
    """Basic parser to clean up LLM results."""
    # Remove any thinking blocks if using models that show them
    text = re.sub(r'<thought>.*?</thought>', '', text, flags=re.DOTALL)
    return text.strip()
