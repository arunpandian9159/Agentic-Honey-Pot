"""
UPI ID Parser for Scam Intelligence Extraction.
"""

import re
from typing import List


class UPIParser:
    """Extracts UPI IDs from text."""
    
    def __init__(self):
        # UPI ID pattern: handle alphanumeric with special chars @ bank/provider
        self.upi_pattern = r'[a-zA-Z0-9\.\-\_]+@[a-zA-Z]+'
        
        # Common email domains to exclude
        self.email_domains = [
            "gmail", "yahoo", "hotmail", "outlook", "email", "mail", 
            "icloud", "protonmail", "zoho", "yandex"
        ]
    
    def parse(self, text: str) -> List[str]:
        """Extract UPI IDs from text."""
        upis = re.findall(self.upi_pattern, text)
        
        # Filter out email-like patterns
        filtered_upis = [
            u for u in upis 
            if not any(domain in u.lower() for domain in self.email_domains)
        ]
        
        return list(set(filtered_upis))
