"""
Bank Account Parser for Scam Intelligence Extraction.
"""

import re
from typing import List


class BankAccountParser:
    """Extracts bank account numbers from text."""
    
    def __init__(self):
        # Bank account pattern (9-18 digit numbers that aren't phone numbers)
        self.account_pattern = r'\b\d{9,18}\b'
    
    def parse(self, text: str) -> List[str]:
        """Extract bank accounts from text."""
        accounts = re.findall(self.account_pattern, text)
        
        # Filter: Exclude typical phone number patterns to reduce false positives
        # Phone numbers in India typically start with 6, 7, 8, 9 and are 10 digits
        filtered_accounts = [
            a for a in accounts 
            if len(a) != 10 or not a.startswith(('6', '7', '8', '9'))
        ]
        
        return list(set(filtered_accounts))
