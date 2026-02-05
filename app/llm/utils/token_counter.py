"""
Token counting utilities for LLM interactions.
"""

from typing import Any, List, Dict


def estimate_tokens(text: str) -> int:
    """
    Roughly estimate tokens based on character count.
    Standard heuristic: 1 token ≈ 4 characters for English.
    """
    if not text:
        return 0
    return len(text) // 4


def count_history_tokens(history: List[Dict[str, str]]) -> int:
    """Estimate tokens for a conversation history."""
    total = 0
    for msg in history:
        content = msg.get("text") or msg.get("content", "")
        total += estimate_tokens(content) + 4  # Overhead for formatting
    return total
