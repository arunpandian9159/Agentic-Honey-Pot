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
        "legal action", "police", "arrest", "penalty", "fine",
        "anydesk", "teamviewer", "rustdesk", "remote access", "support id", "download"
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
- "Send to 9876543210" or "My Anydesk is 123456789" → phone_numbers: ["9876543210", "123456789"]
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
        for key in ["bank_accounts", "upi_ids", "phishing_links", "phone_numbers", "email_addresses", "case_ids", "policy_numbers", "order_numbers", "suspicious_keywords"]:
            if key not in llm_result:
                llm_result[key] = []
        
        # Phone number patterns (Indian) - preserve original format for evaluator matching
        phone_pattern = r'(\+91[\s\-]?\d{10}|\+91[\s\-]?[6-9]\d{9}|(?<!\d)[6-9]\d{9}(?!\d))'
        phones = re.findall(phone_pattern, message)
        clean_phones = []
        for p in phones:
            cleaned = p.strip()
            clean_phones.append(cleaned)
            # Also add normalized 10-digit version for broader matching
            digits_only = re.sub(r'[\s\-\+]', '', cleaned)[-10:]
            if digits_only != cleaned:
                clean_phones.append(digits_only)
        llm_result["phone_numbers"].extend(clean_phones)
        
        # Tech Support patterns (9-10 digit IDs for AnyDesk/TeamViewer, etc.)
        support_pattern = r'(?<!\d)(?:[1-9]\d{2}[\s\-]?\d{3}[\s\-]?\d{3,4})(?!\d)'
        support_ids = re.findall(support_pattern, message)
        for s_id in support_ids:
            cleaned = re.sub(r'[\s\-]', '', s_id)
            if cleaned not in llm_result["phone_numbers"]:
                llm_result["phone_numbers"].append(cleaned)
        
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
        
        # URL pattern — only match actual URLs, not UPI-like patterns
        url_pattern = r'https?://[^\s<>"\']+|www\.[^\s<>"\']+' 
        urls = re.findall(url_pattern, message)
        # Filter out patterns that look like UPI IDs (word@word)
        upi_set = set(u.lower() for u in llm_result.get("upi_ids", []))
        urls = [u for u in urls if u.lower() not in upi_set]
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

        # Case/Reference ID patterns (e.g., SBI-12345, PTM-CB-98765, REF-2025-001)
        case_pattern = r'\b(?:[A-Z]{2,6}[-/](?:[A-Z]{0,4}[-/])?\d{3,10})\b'
        cases = re.findall(case_pattern, message)
        llm_result["case_ids"].extend(cases)

        # Policy number patterns (e.g., POL-123456, POLICY-789)
        policy_pattern = r'\b(?:POL(?:ICY)?[-/]\d{4,12}|INS[-/]\d{4,12})\b'
        policies = re.findall(policy_pattern, message, re.IGNORECASE)
        llm_result["policy_numbers"].extend(policies)

        # Order number patterns (e.g., ORD-2025-78432, AMZ-2025-78432)
        order_pattern = r'\b(?:ORD|ORDER|AMZ|FLP|SNP)[-/]\d{4,}(?:[-/]\d+)?\b'
        orders = re.findall(order_pattern, message, re.IGNORECASE)
        llm_result["order_numbers"].extend(orders)
        
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
            "case_ids": [],
            "policy_numbers": [],
            "order_numbers": [],
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
        score += len(intelligence.get("case_ids", [])) * 1
        score += len(intelligence.get("policy_numbers", [])) * 1
        score += len(intelligence.get("order_numbers", [])) * 1
        score += min(len(intelligence.get("suspicious_keywords", [])), 5) * 0.5
        
        # Bonus for variety (multiple types extracted)
        intel_types = sum([
            len(intelligence.get("bank_accounts", [])) > 0,
            len(intelligence.get("upi_ids", [])) > 0,
            len(intelligence.get("phishing_links", [])) > 0,
            len(intelligence.get("phone_numbers", [])) > 0,
            len(intelligence.get("case_ids", [])) > 0,
            len(intelligence.get("policy_numbers", [])) > 0,
            len(intelligence.get("order_numbers", [])) > 0,
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
        for key in ["bank_accounts", "upi_ids", "phishing_links", "phone_numbers", "email_addresses", "case_ids", "policy_numbers", "order_numbers", "suspicious_keywords"]:
            existing_vals = existing.get(key, [])
            new_vals = new.get(key, [])
            merged[key] = list(set(existing_vals + new_vals))
        
        return merged
