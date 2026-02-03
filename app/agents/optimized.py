"""
Optimized Honeypot Agent - Single LLM call for detection + extraction + response.
Reduces API calls from 3 to 1 per message to stay within Groq rate limits.

Rate Limits: RPM-30, RPD-1K, TPM-12K, TPD-100K
"""

import json
import logging
from typing import Dict, List, Optional

from app.core.llm import GroqClient
from app.agents.personas import PersonaManager

logger = logging.getLogger(__name__)


class OptimizedAgent:
    """
    Combined agent that performs detection, extraction, and response in ONE call.
    This reduces LLM requests from 3 per message to 1.
    """
    
    # Scam indicators for fallback
    SCAM_KEYWORDS = [
        "urgent", "blocked", "suspended", "verify", "account", "bank", "upi",
        "prize", "winner", "lottery", "claim", "fee", "payment", "otp", "kyc",
        "microsoft", "virus", "hacked", "job", "selected", "salary", "http"
    ]
    
    def __init__(self, llm_client: GroqClient):
        self.llm = llm_client
        self.persona_manager = PersonaManager()
    
    async def process_message(
        self,
        scammer_message: str,
        session: Dict,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Process scammer message in a single LLM call.
        Returns detection result, extracted intel, and response.
        
        Args:
            scammer_message: The scammer's message
            session: Current session state
            metadata: Optional request metadata
        
        Returns:
            Dict with: is_scam, scam_type, confidence, intelligence, response
        """
        # Get persona (use existing or select based on quick keyword check)
        persona = session.get("persona")
        if not persona:
            # Quick keyword-based scam type detection for persona selection
            scam_type = self._quick_scam_type(scammer_message)
            persona = self.persona_manager.select_persona(scam_type, "medium")
        
        persona_prompt = self.persona_manager.get_persona_prompt(persona)
        
        # Build conversation context (last 3 messages only to save tokens)
        history = session.get("conversation_history", [])[-3:]
        history_text = self._format_history(history) if history else "[First message]"
        
        # Determine stage from message count
        msg_count = session.get("message_count", 0)
        stage_tactic = self._get_stage_tactic(msg_count)
        
        # Combined prompt - detection + extraction + response in ONE
        prompt = f"""Analyze and respond. Output ONLY valid JSON.

                MSG: "{scammer_message}"
                HISTORY: {history_text}
                PERSONA: {persona_prompt[:200]}
                TACTIC: {stage_tactic}

                JSON output:
                {{"is_scam":true/false,"confidence":0.0-1.0,"scam_type":"bank_fraud|upi_fraud|phishing|job_scam|lottery|investment|tech_support|other","intel":{{"bank_accounts":[],"upi_ids":[],"phone_numbers":[],"links":[]}},"response":"victim reply 1-2 sentences"}}

                SCAM SIGNS: urgency, threats, payment requests, OTP/KYC, prizes, job offers
                EXTRACT: UPI IDs (x@bank), phones (10 digits), links (http), accounts (12+ digits)
                RESPONSE RULES: Stay in persona, keep scammer engaged, ask for their payment details"""

        try:
            response = await self.llm.generate_json(prompt=prompt, max_tokens=250)
            result = json.loads(response)
            
            # Validate and normalize
            result = self._normalize_result(result, persona)
            
            logger.info(
                f"Combined result: scam={result['is_scam']}, "
                f"type={result['scam_type']}, intel_count={self._count_intel(result['intel'])}"
            )
            
            return result
            
        except Exception as e:
            logger.warning(f"Combined processing failed: {e}")
            return self._fallback_response(scammer_message, persona, msg_count)
    
    def _quick_scam_type(self, message: str) -> str:
        """Quick keyword-based scam type detection (no LLM)."""
        msg_lower = message.lower()
        
        if any(kw in msg_lower for kw in ["bank", "account", "kyc", "sbi", "hdfc"]):
            return "bank_fraud"
        elif any(kw in msg_lower for kw in ["upi", "@", "paytm", "phonepe"]):
            return "upi_fraud"
        elif any(kw in msg_lower for kw in ["http", "link", "click", "www"]):
            return "phishing"
        elif any(kw in msg_lower for kw in ["job", "selected", "salary", "hiring"]):
            return "job_scam"
        elif any(kw in msg_lower for kw in ["prize", "winner", "lottery", "won"]):
            return "lottery"
        elif any(kw in msg_lower for kw in ["invest", "return", "profit", "double"]):
            return "investment"
        elif any(kw in msg_lower for kw in ["virus", "microsoft", "hacked"]):
            return "tech_support"
        return "other"
    
    def _format_history(self, history: List[Dict]) -> str:
        """Format history concisely."""
        return " | ".join([
            f"{m.get('sender','?')[:1].upper()}: {m.get('text','')[:50]}"
            for m in history
        ])
    
    def _get_stage_tactic(self, msg_count: int) -> str:
        """Get concise stage tactic based on message count."""
        if msg_count <= 2:
            return "Show concern, ask why"
        elif msg_count <= 5:
            return "Build trust, ask for their details"
        elif msg_count <= 8:
            return "Show hesitation, request their payment info"
        elif msg_count <= 12:
            return "Slowly comply, ask for account/UPI again"
        else:
            return "Report issues with their link, prolong"
    
    def _normalize_result(self, result: Dict, persona: str) -> Dict:
        """Normalize and validate result."""
        # Ensure all fields exist
        result.setdefault("is_scam", True)
        result.setdefault("confidence", 0.7)
        result.setdefault("scam_type", "other")
        result.setdefault("intel", {})
        result.setdefault("response", "I don't understand. Can you explain?")
        
        # Normalize intel structure
        intel = result["intel"]
        intel.setdefault("bank_accounts", [])
        intel.setdefault("upi_ids", [])
        intel.setdefault("phone_numbers", [])
        intel.setdefault("links", [])
        intel.setdefault("suspicious_keywords", [])
        
        # Rename for compatibility
        if "phishing_links" not in intel and "links" in intel:
            intel["phishing_links"] = intel.pop("links")
        
        result["persona"] = persona
        
        return result
    
    def _count_intel(self, intel: Dict) -> int:
        """Count total intelligence items."""
        return sum(len(v) for v in intel.values() if isinstance(v, list))
    
    def _fallback_response(self, message: str, persona: str, msg_count: int) -> Dict:
        """Generate fallback result without LLM."""
        import re
        
        msg_lower = message.lower()
        
        # Check if scam using keywords
        matches = [kw for kw in self.SCAM_KEYWORDS if kw in msg_lower]
        is_scam = len(matches) >= 2
        
        # Extract intel with regex
        intel = {
            "bank_accounts": re.findall(r'\b\d{10,18}\b', message),
            "upi_ids": [u for u in re.findall(r'[\w\.\-]+@[\w]+', message) 
                       if not any(d in u.lower() for d in ["gmail", "yahoo", "outlook"])],
            "phone_numbers": re.findall(r'[6-9]\d{9}', message),
            "phishing_links": re.findall(r'https?://\S+', message),
            "suspicious_keywords": matches[:5]
        }
        
        # Fallback responses by stage
        if msg_count <= 2:
            response = "What happened? Why is my account blocked?"
        elif msg_count <= 5:
            response = "I see, that's serious. What do I need to do?"
        elif msg_count <= 8:
            response = "Before I do anything, can you verify who you are?"
        elif msg_count <= 12:
            response = "Okay, I'll do it. Where should I send the payment?"
        else:
            response = "The link isn't working. Can you send it again?"
        
        return {
            "is_scam": is_scam,
            "confidence": min(len(matches) * 0.2, 0.9),
            "scam_type": self._quick_scam_type(message),
            "intel": intel,
            "response": response,
            "persona": persona
        }
