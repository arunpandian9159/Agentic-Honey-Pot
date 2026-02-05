"""
Optimized Honeypot Agent - Single LLM call for detection + extraction + response.
Reduces API calls from 3 to 1 per message to stay within Groq rate limits.

Rate Limits: RPM-30, RPD-1K, TPM-12K, TPD-100K
"""

import json
import logging
import random
from typing import Dict, List, Optional

from app.core.llm import GroqClient
from app.agents.personas import PersonaManager
from app.agents.enhanced_personas import ENHANCED_PERSONAS, get_persona
from app.agents.response_variation import ResponseVariationEngine
from app.agents.natural_flow import get_stage_guidance
from app.agents.context_aware import get_concise_context

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
        self.variation_engine = ResponseVariationEngine()
    
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
        session_id = session.get("session_id", "unknown")
        
        # Get persona (use existing or select enhanced persona)
        persona_name = session.get("persona")
        if not persona_name:
            # Quick keyword-based scam type detection for persona selection
            scam_type = self._quick_scam_type(scammer_message)
            persona_name = self._select_enhanced_persona(scam_type)
        
        # Use enhanced persona for prompt if available
        if persona_name in ENHANCED_PERSONAS:
            enhanced_persona = get_persona(persona_name)
            persona_prompt = enhanced_persona.get("enhanced_system_prompt", "")[:300]
        else:
            persona_prompt = self.persona_manager.get_persona_prompt(persona_name)
        
        # Build conversation context (last 3 messages only to save tokens)
        history = session.get("conversation_history", [])[-3:]
        history_text = self._format_history(history) if history else "[First message]"
        
        # Determine stage from message count
        msg_count = session.get("message_count", 0)
        stage_tactic = get_stage_guidance(msg_count)
        context_hint = get_concise_context(session, msg_count)
        
        # Combined prompt - detection + extraction + response with human-like guidance
        prompt = f"""Analyze and respond. Output ONLY valid JSON.

MSG: "{scammer_message}"
HISTORY: {history_text}
PERSONA: {persona_prompt[:300]}
TACTIC: {stage_tactic}
{context_hint}

JSON output:
{{"is_scam":true/false,"confidence":0.0-1.0,"scam_type":"bank_fraud|upi_fraud|phishing|job_scam|lottery|investment|tech_support|other","intel":{{"bank_accounts":[],"upi_ids":[],"phone_numbers":[],"links":[]}},"response":"victim reply 1-2 sentences"}}

SCAM SIGNS: urgency, threats, payment requests, OTP/KYC, prizes, job offers
EXTRACT: UPI IDs (x@bank), phones (10 digits), links (http), accounts (12+ digits)
RESPONSE RULES:
- Sound like a REAL person, not an AI
- Use persona-appropriate language and imperfections
- Vary response style from previous messages
- Keep scammer engaged, extract their payment details"""

        try:
            response = await self.llm.generate_json(prompt=prompt, max_tokens=250)
            result = json.loads(response)
            
            # Validate and normalize (includes fragment/short reply check)
            result = self._normalize_result(result, persona_name, msg_count)
            
            # Apply humanization if using enhanced persona
            if persona_name in ENHANCED_PERSONAS and result.get("response"):
                result["response"] = self.variation_engine.humanize_response(
                    base_response=result["response"],
                    persona_name=persona_name,
                    session_id=session_id,
                    message_number=msg_count
                )
                # Re-validate after humanization (it can truncate); replace fragment with fallback
                if not self._is_valid_response(result["response"]):
                    result["response"] = self.variation_engine.get_fallback_response(
                        persona_name=persona_name,
                        conversation_stage=get_stage_guidance(msg_count)
                    )
            
            logger.info(
                f"Combined result: scam={result['is_scam']}, "
                f"type={result['scam_type']}, persona={persona_name}, intel_count={self._count_intel(result['intel'])}"
            )
            
            return result
            
        except Exception as e:
            logger.warning(f"Combined processing failed: {e}")
            return self._fallback_response(scammer_message, persona_name, msg_count)
    
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
    
    def _select_enhanced_persona(self, scam_type: str) -> str:
        """Select appropriate enhanced persona based on scam type."""
        persona_mapping = {
            "bank_fraud": ["elderly_confused", "tech_naive_parent"],
            "upi_fraud": ["elderly_confused", "tech_naive_parent", "busy_professional"],
            "phishing": ["elderly_confused", "curious_student", "tech_naive_parent"],
            "job_scam": ["desperate_job_seeker", "curious_student"],
            "lottery": ["elderly_confused", "curious_student"],
            "investment": ["busy_professional", "curious_student"],
            "tech_support": ["elderly_confused", "tech_naive_parent"],
            "other": ["tech_naive_parent", "curious_student"]
        }
        
        candidates = persona_mapping.get(scam_type, ["tech_naive_parent"])
        return random.choice(candidates)
    
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
    
    # Minimum length and known fragments that indicate truncated/incomplete reply
    MIN_RESPONSE_LEN = 20
    FRAGMENT_PATTERNS = (
        "i'm", "i am", "that", "can", "hello", "ok", "okay", "yes", "no",
        "wait", "what", "why", "how", "when", "sorry", "please", "thanks",
        "i'm not", "i'm confused", "i'm not sure", "hello i'm", "i'm not sure i",
    )

    def _is_valid_response(self, text: str) -> bool:
        """Return False if response looks truncated or fragment-only (e.g. 'I'm', 'that')."""
        if not text or not isinstance(text, str):
            return False
        t = text.strip()
        if len(t) < self.MIN_RESPONSE_LEN:
            return False
        words = t.split()
        if len(words) <= 2:
            return False
        t_lower = t.lower()
        # Exact match to known fragment
        if t_lower in ("i'm", "i am", "that", "can", "hello", "ok", "okay", "yes", "no", "wait", "what", "why", "how"):
            return False
        for frag in self.FRAGMENT_PATTERNS:
            if t_lower == frag:
                return False
        return True

    def _normalize_result(self, result: Dict, persona: str, msg_count: int = 0) -> Dict:
        """Normalize and validate result. Replace fragment/short responses with fallback."""
        # Ensure all fields exist
        result.setdefault("is_scam", True)
        result.setdefault("confidence", 0.7)
        result.setdefault("scam_type", "other")
        result.setdefault("intel", {})
        result.setdefault("response", "I don't understand. Can you explain?")
        
        # Replace truncated or fragment-like response with fallback
        if not self._is_valid_response(result["response"]):
            result["response"] = self.variation_engine.get_fallback_response(
                persona_name=persona,
                conversation_stage=get_stage_guidance(msg_count)
            )
            logger.info("Replaced fragment/short response with fallback")
        
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
            response = "What happened Why is my account blocked?"
        elif msg_count <= 5:
            response = "I see that its serious. What should I do?"
        elif msg_count <= 8:
            response = "Before I do anything can you verify who you are?"
        elif msg_count <= 12:
            response = "Okay I'll do it. Where should I send the payment?"
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
