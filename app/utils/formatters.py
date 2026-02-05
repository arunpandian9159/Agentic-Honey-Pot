"""
Formatting utilities for AI Honeypot API.
"""

import re
from datetime import datetime
from typing import Any, Dict


def format_timestamp(ts: int) -> str:
    """Format unix timestamp (ms) to readable string."""
    dt = datetime.fromtimestamp(ts / 1000)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def clean_llm_output(text: str) -> str:
    """Clean LLM output by removing quotes, tags, etc."""
    text = text.strip()
    # Remove surrounding quotes if they exist
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        text = text[1:-1]
    
    # Remove common AI prefixes
    prefixes = ["Response:", "Reply:", "Victim:", "Bot:"]
    for prefix in prefixes:
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
            
    return text.strip()


def truncate_text(text: str, max_len: int = 100) -> str:
    """Truncate text for logging or display."""
    if len(text) <= max_len:
        return text
    return text[:max_len-3] + "..."
