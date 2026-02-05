"""
URL Parser for Scam Intelligence Extraction.
"""

import re
from typing import List


class URLParser:
    """Extracts URLs and phishing links from text."""
    
    def __init__(self):
        # Comprehensive URL pattern
        self.url_pattern = r'https?://[^\s<>"\']+|www\.[^\s<>"\']+|[a-zA-Z0-9\-]+\.[a-zA-Z]{2,}[/\w\.\-\?\=\&]*'
    
    def parse(self, text: str) -> List[str]:
        """Extract URLs from text."""
        urls = re.findall(self.url_pattern, text)
        
        # Basic validation: filter out small false positives like "i.e." or "p.m."
        valid_urls = []
        for url in urls:
            # Simple heuristic: must have at least one dot and not be extremely short
            if "." in url and len(url) > 4:
                # Basic cleanup
                cleaned = url.strip(".,!?;:")
                valid_urls.append(cleaned)
                
        return list(set(valid_urls))
