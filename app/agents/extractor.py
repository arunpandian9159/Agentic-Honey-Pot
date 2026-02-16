"""
Intelligence Extraction System for AI Honeypot API.
Extracts scam artifacts like bank accounts, UPI IDs, phone numbers, and phishing links.
"""

import json
import re
import logging
from typing import Dict, List

from app.core.llm import GroqClient

logger = logging.getLogger(__name__)


class IntelligenceExtractor:
    """Extracts intelligence from scammer messages using LLM and regex."""
    
    # Common scam keywords for context
    SCAM_KEYWORDS = [
        "urgent", "immediately", "verify", "blocked", "suspended", "expired",
        "prize", "won", "winner", "claim", "free", "gift", "offer",
        "account", "bank", "upi", "payment", "transfer", "send money",
        "otp", "password", "pin", "cvv", "confirm", "update", "kyc",
        "legal action", "police", "arrest", "penalty", "fine"
    ]
    
    def __init__(self, llm_client: GroqClient):
        self.llm = llm_client
    
    async def extract(self, message: str) -> Dict:
        """
        Extract intelligence from a scammer's message.
        
        Args:
            message: The scammer's message text
        
        Returns:
            Dictionary with extracted intelligence
        """
        prompt = f"""Extract scam intelligence from this message. Respond ONLY with valid JSON.

Message: "{message}"

Extract these items if present:
{{
  "bank_accounts": ["Account numbers, IFSC codes, or bank details"],
  "upi_ids": ["phone@upi, name@bank format UPI IDs"],
  "phishing_links": ["http:// or https:// URLs"],
  "phone_numbers": ["+91XXXXXXXXXX or 10-digit numbers"],
  "email_addresses": ["user@domain.com format emails"],
  "suspicious_keywords": ["urgent", "verify", "blocked", "prize", etc.]
}}

Rules:
- Only include items explicitly present in the message
- Normalize formats (remove spaces from numbers)
- For UPI IDs, look for patterns like name@bankname, number@paytm, etc.
- For phone numbers, include both +91 and 10-digit formats
- Empty arrays if nothing found
- Be thorough - check for partial mentions

Examples:
- "Send to 9876543210" → phone_numbers: ["9876543210"]
- "Pay to winner@paytm" → upi_ids: ["winner@paytm"]
- "Click http://scam.com" → phishing_links: ["http://scam.com"]
- "Account 1234567890123" → bank_accounts: ["1234567890123"]
"""
        
        try:
            response = await self.llm.generate_json(prompt=prompt, temperature=0.0)
            result = json.loads(response)
            
            # Enhance with regex-based extraction
            result = self._enhance_with_regex(message, result)
            
            logger.info(f"Extracted intelligence: {self._summarize_intel(result)}")
            return result
            
        except Exception as e:
            logger.warning(f"LLM extraction failed, using regex fallback: {str(e)}")
            return self._regex_extraction(message)
    
    def _enhance_with_regex(self, message: str, llm_result: Dict) -> Dict:
        """
        Enhance LLM extraction with regex patterns.
        
        Args:
            message: Original message
            llm_result: LLM extraction result
        
        Returns:
            Enhanced extraction result
        """
        # Ensure all keys exist
        for key in ["bank_accounts", "upi_ids", "phishing_links", "phone_numbers", "email_addresses", "suspicious_keywords"]:
            if key not in llm_result:
                llm_result[key] = []
        
        # Phone number patterns (Indian)
        phone_pattern = r'(?:\+91[\s\-]?)?[6-9]\d{9}'
        phones = re.findall(phone_pattern, message)
        clean_phones = [
            re.sub(r'[\s\-\+]', '', p)[-10:]
            for p in phones
            if len(re.sub(r'[\s\-\+]', '', p)) >= 10
        ]
        llm_result["phone_numbers"].extend(clean_phones)
        
        # Email address pattern
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, message)
        llm_result["email_addresses"].extend(emails)

        # UPI ID pattern
        upi_pattern = r'[a-zA-Z0-9\.\-\_]+@[a-zA-Z]+'
        upis = re.findall(upi_pattern, message)
        # Filter out email-like patterns (those with common email domains)
        email_domains = ["gmail", "yahoo", "hotmail", "outlook", "email", "mail", "com", "org", "net", "in", "co"]
        upis = [u for u in upis if not any(d in u.lower() for d in email_domains)]
        llm_result["upi_ids"].extend(upis)
        
        # URL pattern
        url_pattern = r'https?://[^\s<>"\']+|www\.[^\s<>"\']+|[a-zA-Z0-9\-]+\.[a-zA-Z]{2,}[/\w\.\-\?\=\&]*'
        urls = re.findall(url_pattern, message)
        llm_result["phishing_links"].extend(urls)
        
        # Bank account pattern (9-18 digit numbers that aren't phone numbers)
        account_pattern = r'\b\d{9,18}\b'
        accounts = re.findall(account_pattern, message)
        # Exclude phone numbers
        accounts = [a for a in accounts if len(a) != 10 or not a.startswith(('6', '7', '8', '9'))]
        llm_result["bank_accounts"].extend(accounts)
        
        # Extract keywords
        message_lower = message.lower()
        keywords = [kw for kw in self.SCAM_KEYWORDS if kw in message_lower]
        llm_result["suspicious_keywords"].extend(keywords)
        
        # Deduplicate all lists
        for key in llm_result:
            if isinstance(llm_result[key], list):
                llm_result[key] = list(set(llm_result[key]))
        
        return llm_result
    
    def _regex_extraction(self, message: str) -> Dict:
        """
        Pure regex-based fallback extraction.
        
        Args:
            message: The message to analyze
        
        Returns:
            Extraction result
        """
        result = {
            "bank_accounts": [],
            "upi_ids": [],
            "phishing_links": [],
            "phone_numbers": [],
            "email_addresses": [],
            "suspicious_keywords": []
        }
        
        return self._enhance_with_regex(message, result)
    
    def _summarize_intel(self, intel: Dict) -> str:
        """Create a brief summary of extracted intelligence."""
        parts = []
        for key, values in intel.items():
            if values:
                parts.append(f"{key}: {len(values)}")
        return ", ".join(parts) if parts else "none"
    
    def calculate_score(self, intelligence: Dict) -> float:
        """
        Calculate intelligence quality score.
        
        Scoring:
        - Bank accounts: 3 points each (highest value)
        - UPI IDs: 2 points each
        - Phishing links: 2 points each
        - Phone numbers: 1 point each
        - Suspicious keywords: 0.5 points each (max 5)
        - Bonus 1.2x if 3+ different types extracted
        
        Args:
            intelligence: Extracted intelligence dictionary
        
        Returns:
            Quality score as float
        """
        score = 0.0
        
        # Calculate base score
        score += len(intelligence.get("bank_accounts", [])) * 3
        score += len(intelligence.get("upi_ids", [])) * 2
        score += len(intelligence.get("phishing_links", [])) * 2
        score += len(intelligence.get("phone_numbers", [])) * 1
        score += min(len(intelligence.get("suspicious_keywords", [])), 5) * 0.5
        
        # Bonus for variety (multiple types extracted)
        intel_types = sum([
            len(intelligence.get("bank_accounts", [])) > 0,
            len(intelligence.get("upi_ids", [])) > 0,
            len(intelligence.get("phishing_links", [])) > 0,
            len(intelligence.get("phone_numbers", [])) > 0
        ])
        
        if intel_types >= 3:
            score *= 1.2  # 20% bonus for variety
        
        return round(score, 2)
    
    def merge_intelligence(self, existing: Dict, new: Dict) -> Dict:
        """
        Merge new intelligence with existing, deduplicating entries.
        
        Args:
            existing: Existing intelligence dictionary
            new: New intelligence to merge
        
        Returns:
            Merged intelligence dictionary
        """
        merged = {}
        for key in ["bank_accounts", "upi_ids", "phishing_links", "phone_numbers", "email_addresses", "suspicious_keywords"]:
            existing_vals = existing.get(key, [])
            new_vals = new.get(key, [])
            merged[key] = list(set(existing_vals + new_vals))
        
        return merged
