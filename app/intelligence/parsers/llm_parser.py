"""
LLM-based Intelligence Parser for Scam Intelligence Extraction.
"""

import json
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class LLMParser:
    """Extracts intelligence using LLM analysis."""
    
    def __init__(self, llm_client):
        self.llm = llm_client
    
    async def parse(self, message: str) -> Dict[str, List[str]]:
        """
        Extract intelligence from a scammer's message using LLM.
        """
        prompt = f"""Extract scam intelligence from this message. Respond ONLY with valid JSON.

Message: "{message}"

Extract these items if present:
{{
  "bank_accounts": ["Account numbers, IFSC codes, or bank details"],
  "upi_ids": ["phone@upi, name@bank format UPI IDs"],
  "phishing_links": ["http:// or https:// URLs"],
  "phone_numbers": ["+91XXXXXXXXXX or 10-digit numbers"],
  "suspicious_keywords": ["urgent", "verify", "blocked", "prize", etc.]
}}

Rules:
- Only include items explicitly present in the message
- Normalize formats (remove spaces from numbers)
- For UPI IDs, look for patterns like name@bankname, number@paytm, etc.
- Empty arrays if nothing found
- Be thorough - check for partial mentions
"""
        
        try:
            response = await self.llm.generate_json(prompt=prompt, temperature=0.0)
            result = json.loads(response)
            
            # Ensure all keys exist
            for key in ["bank_accounts", "upi_ids", "phishing_links", "phone_numbers", "suspicious_keywords"]:
                if key not in result or not isinstance(result[key], list):
                    result[key] = []
                    
            return result
            
        except Exception as e:
            logger.warning(f"LLM intelligence extraction failed: {str(e)}")
            return {
                "bank_accounts": [],
                "upi_ids": [],
                "phishing_links": [],
                "phone_numbers": [],
                "suspicious_keywords": []
            }
