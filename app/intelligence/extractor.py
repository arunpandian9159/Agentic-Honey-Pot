"""
Intelligence Extraction Orchestrator for AI Honeypot API.
Orchestrates multiple parsers to extract artifacts from scam messages.
"""

import logging
from typing import Dict, List, Optional

from app.intelligence.parsers.bank_parser import BankAccountParser
from app.intelligence.parsers.upi_parser import UPIParser
from app.intelligence.parsers.phone_parser import PhoneParser
from app.intelligence.parsers.url_parser import URLParser
from app.intelligence.parsers.llm_parser import LLMParser

logger = logging.getLogger(__name__)


class IntelligenceExtractor:
    """
    Orchestrates scam intelligence extraction.
    
    Combines LLM-based extraction with specialized regex-based parsers.
    """
    
    # Common scam keywords for context
    SCAM_KEYWORDS = [
        "urgent", "immediately", "verify", "blocked", "suspended", "expired",
        "prize", "won", "winner", "claim", "free", "gift", "offer",
        "account", "bank", "upi", "payment", "transfer", "send money",
        "otp", "password", "pin", "cvv", "confirm", "update", "kyc",
        "legal action", "police", "arrest", "penalty", "fine"
    ]
    
    def __init__(self, llm_client):
        self.bank_parser = BankAccountParser()
        self.upi_parser = UPIParser()
        self.phone_parser = PhoneParser()
        self.url_parser = URLParser()
        self.llm_parser = LLMParser(llm_client)
    
    async def extract(self, message: str) -> Dict[str, List[str]]:
        """
        Extract intelligence from a scammer's message.
        """
        logger.info(f"Extracting intelligence from message: {message[:50]}...")
        
        # 1. Start with LLM extraction
        result = await self.llm_parser.parse(message)
        
        # 2. Enhance with regex-based parsers
        result["bank_accounts"].extend(self.bank_parser.parse(message))
        result["upi_ids"].extend(self.upi_parser.parse(message))
        result["phone_numbers"].extend(self.phone_parser.parse(message))
        result["phishing_links"].extend(self.url_parser.parse(message))
        
        # 3. Extract keywords
        message_lower = message.lower()
        keywords = [kw for kw in self.SCAM_KEYWORDS if kw in message_lower]
        result["suspicious_keywords"].extend(keywords)
        
        # 4. Deduplicate all lists
        for key in result:
            if isinstance(result[key], list):
                result[key] = sorted(list(set(result[key])))
        
        logger.info(f"Extracted Artifacts: " + 
                    ", ".join([f"{k}: {len(v)}" for k, v in result.items() if v]))
        
        return result
    
    def calculate_score(self, intelligence: Dict) -> float:
        """
        Calculate intelligence quality score.
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
        """
        merged = {}
        target_keys = ["bank_accounts", "upi_ids", "phishing_links", "phone_numbers", "suspicious_keywords"]
        for key in target_keys:
            existing_vals = existing.get(key, [])
            new_vals = new.get(key, [])
            merged[key] = sorted(list(set(existing_vals + new_vals)))
        
        return merged
