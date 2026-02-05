"""
Common validation utilities for AI Honeypot API.
"""

import re


def is_valid_phone(phone: str) -> bool:
    """Basic validation for Indian phone numbers."""
    return bool(re.match(r'^[6-9]\d{9}$', phone))


def is_valid_upi(upi: str) -> bool:
    """Basic validation for UPI IDs."""
    return bool(re.match(r'^[a-zA-Z0-9\.\-\_]+@[a-zA-Z]+$', upi))


def is_valid_url(url: str) -> bool:
    """Basic validation for URLs."""
    pattern = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return bool(re.match(pattern, url))
