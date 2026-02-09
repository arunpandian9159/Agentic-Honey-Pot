"""
Scam Detection Agent for AI Honeypot API.
Analyzes messages to detect scam intent using LLM and fallback keyword matching.
"""

import json
import logging
from typing import Dict, List, Optional

from app.core.llm import GroqClient

logger = logging.getLogger(__name__)


class ScamDetector:
    """Detects scam messages using LLM analysis with keyword fallback."""
    
    # Common scam keywords for fallback detection
    SCAM_KEYWORDS = [
        # Urgency/threats
        "urgent", "immediately", "today", "blocked", "suspended", "deactivated",
        "expire", "expired", "expires", "penalty", "legal action", "arrest", "police",
        # Authority impersonation
        "sbi", "hdfc", "icici", "rbi", "bank", "customer care", "microsoft", "apple",
        # Financial
        "upi", "account", "transfer", "pay", "payment", "send money", "fee",
        "refund", "cashback", "processing fee", "registration fee", "training fee",
        # Personal info
        "verify", "kyc", "otp", "cvv", "pin", "password", "confirm", "update",
        # Offers/prizes
        "won", "winner", "prize", "lottery", "lucky draw", "congratulations",
        "gift card", "free", "claim", "cashback",
        # Investment scams
        "investment", "guaranteed", "returns", "double", "crypto", "profit",
        # Job scams
        "selected", "shortlisted", "job", "work from home", "salary", "hiring",
        # Phishing
        "click", "link", "http", "www", "download",
        # Tech support
        "virus", "hacked", "compromised", "alert", "security"
    ]
    
    def __init__(self, llm_client: GroqClient):
        self.llm = llm_client
    
    async def analyze(
        self,
        message: str,
        history: Optional[List] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Analyze a message for scam intent.
        
        Args:
            message: The text message to analyze
            history: Previous conversation history
            metadata: Request metadata (channel, language, etc.)
        
        Returns:
            Detection result with is_scam, confidence, scam_type, urgency_level, key_indicators
        """
        channel = metadata.get("channel", "Unknown") if metadata else "Unknown"
        context = "First message" if not history else f"{len(history)} previous messages"
        
        prompt = f"""You are a scam detection system. Analyze this message and respond ONLY with valid JSON.

Message: "{message}"
Channel: {channel}
Context: {context}

Respond with this exact JSON structure:
{{
  "is_scam": true or false,
  "confidence": 0.0 to 1.0,
  "scam_type": "bank_fraud | upi_fraud | phishing | fake_offer | tech_support | lottery | romance | investment | job_scam | other",
  "urgency_level": "low | medium | high | critical",
  "key_indicators": ["indicator1", "indicator2"]
}}

Scam indicators to look for:
- Urgency/threats: "account blocked", "immediate action", "today only", "legal action"
- Authority impersonation: "bank", "government", "police", "IT department", "RBI"
- Payment requests: UPI IDs, bank accounts, "send money", "pay fees", "transfer"
- Personal info requests: "verify", "share OTP", "confirm details", "KYC update"
- Links: suspicious URLs, shortened links, fake domains
- Too-good offers: "won prize", "free gift", "guaranteed returns", "double money"
- Fear tactics: "suspended", "penalty", "arrest", "blocked"
- Job scams: "selected", "registration fee", "training fee", "work from home"

Be confident in detection (>0.7) if multiple indicators present.
For clear scam patterns, set confidence to 0.85+.
"""
        
        try:
            response = await self.llm.generate_json(prompt=prompt, temperature=0.1)
            
            # Parse JSON response
            result = json.loads(response)
            
            # Validate response structure
            required_keys = ["is_scam", "confidence", "scam_type", "urgency_level", "key_indicators"]
            if not all(key in result for key in required_keys):
                raise ValueError("Invalid detection response structure")
            
            # Ensure confidence is float
            result["confidence"] = float(result["confidence"])
            
            logger.info(
                f"Scam detection result: is_scam={result['is_scam']}, "
                f"confidence={result['confidence']:.2f}, type={result['scam_type']}"
            )
            
            return result
            
        except Exception as e:
            logger.warning(f"LLM detection failed, using fallback: {str(e)}")
            return self._fallback_detection(message)
    
    # Keyword-to-scam-type mapping for fallback classification
    SCAM_TYPE_KEYWORDS = {
        "bank_fraud": ["bank", "account", "kyc"],
        "upi_fraud": ["upi", "@"],
        "phishing": ["http", "link", "click"],
        "lottery": ["prize", "lottery", "winner"],
        "job_scam": ["job", "work from home", "registration"],
        "investment": ["investment", "returns", "double"],
        "tech_support": ["virus", "microsoft", "tech support"],
    }

    def _fallback_detection(self, message: str) -> Dict:
        """Simple keyword-based fallback detection if LLM fails."""
        message_lower = message.lower()

        matches = [kw for kw in self.SCAM_KEYWORDS if kw in message_lower]
        confidence = min(len(matches) * 0.20, 0.95)

        # Determine scam type from keywords
        scam_type = "other"
        for stype, keywords in self.SCAM_TYPE_KEYWORDS.items():
            if any(kw in message_lower for kw in keywords):
                scam_type = stype
                break

        # Determine urgency
        if any(kw in message_lower for kw in ["blocked", "suspended", "arrest", "legal"]):
            urgency = "critical"
        elif any(kw in message_lower for kw in ["urgent", "immediately", "now", "today"]):
            urgency = "high"
        elif len(matches) >= 3:
            urgency = "medium"
        else:
            urgency = "low"

        result = {
            "is_scam": len(matches) >= 2,
            "confidence": confidence,
            "scam_type": scam_type,
            "urgency_level": urgency,
            "key_indicators": matches[:5]
        }

        logger.info(f"Fallback detection result: {result}")
        return result
