"""
Phone Number Parser for Scam Intelligence Extraction.
"""

import re
from typing import List


class PhoneParser:
    """Extracts phone numbers from text (primarily Indian format)."""
    
    def __init__(self):
        # Indian phone number patterns
        self.phone_pattern = r'(?:\+91[\s\-]?)?[6-9]\d{9}'
    
    def parse(self, text: str) -> List[str]:
        """Extract and normalize phone numbers from text."""
        phones = re.findall(self.phone_pattern, text)
        
        clean_phones = []
        for p in phones:
            # Remove symbols
            cleaned = re.sub(r'[\s\-\+]', '', p)
            
            # Remove country code if present at the start
            if cleaned.startswith('91') and len(cleaned) > 10:
                cleaned = cleaned[2:]
            
            # Ensure it is a valid length (typically 10 for India)
            if len(cleaned) >= 10:
                clean_phones.append(cleaned[-10:])
                
        return list(set(clean_phones))
