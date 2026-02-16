"""
Optimized Honeypot Agent - Single LLM call for detection + extraction + response.
Reduces API calls from 3 to 1 per message to stay within Groq rate limits.

Rate Limits: RPM-30, RPD-1K, TPM-12K, TPD-100K
"""

import json
import logging
import random
import re
from typing import Dict, List, Optional

from app.core.llm import GroqClient
from app.core.config import settings
from app.agents.personas import PersonaManager
from app.agents.enhanced_personas import ENHANCED_PERSONAS, get_persona
from app.agents.response_variation import ResponseVariationEngine
from app.agents.natural_flow import get_stage_guidance
from app.agents.context_aware import get_concise_context
from app.agents.scammer_profiler import ScammerProfiler
from app.agents.extraction_strategies import get_extraction_prompt_hint

logger = logging.getLogger(__name__)

# Minimum response length and known fragment patterns
MIN_RESPONSE_LEN = 20
KNOWN_FRAGMENTS = frozenset([
    "i'm", "i am", "that", "can", "hello", "ok", "okay", "yes", "no",
    "wait", "what", "why", "how", "when", "sorry", "please", "thanks",
    "i'm not", "i'm confused", "i'm not sure", "hello i'm", "i'm not sure i",
])

# Scam indicators for fallback detection
SCAM_KEYWORDS = [
    "urgent", "blocked", "suspended", "verify", "account", "bank", "upi",
    "prize", "winner", "lottery", "claim", "fee", "payment", "otp", "kyc",
    "microsoft", "virus", "hacked", "job", "selected", "salary", "http"
]

# Scam type detection keywords
SCAM_TYPE_KEYWORDS = {
    "bank_fraud": ["bank", "account", "kyc", "sbi", "hdfc"],
    "upi_fraud": ["upi", "@", "paytm", "phonepe"],
    "phishing": ["http", "link", "click", "www"],
    "job_scam": ["job", "selected", "salary", "hiring"],
    "lottery": ["prize", "winner", "lottery", "won"],
    "investment": ["invest", "return", "profit", "double"],
    "tech_support": ["virus", "microsoft", "hacked"],
}

# Persona selection mapping by scam type
PERSONA_MAPPING = {
    "bank_fraud": ["elderly_confused", "tech_naive_parent"],
    "upi_fraud": ["elderly_confused", "tech_naive_parent", "busy_professional"],
    "phishing": ["elderly_confused", "curious_student", "tech_naive_parent"],
    "job_scam": ["desperate_job_seeker", "curious_student"],
    "lottery": ["elderly_confused", "curious_student"],
    "investment": ["busy_professional", "curious_student"],
    "tech_support": ["elderly_confused", "tech_naive_parent"],
    "other": ["tech_naive_parent", "curious_student"]
}


class OptimizedAgent:
    """
    Combined agent that performs detection, extraction, and response in ONE call.
    This reduces LLM requests from 3 per message to 1.
    """

    def __init__(self, llm_client: GroqClient):
        self.llm = llm_client
        self.persona_manager = PersonaManager()
        self.variation_engine = ResponseVariationEngine()
        self.scammer_profiler = ScammerProfiler()

    async def process_message(
        self,
        scammer_message: str,
        session: Dict,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Process scammer message in a single LLM call.
        Returns detection result, extracted intel, and response.
        """
        session_id = session.get("session_id", "unknown")

        # Get persona (use existing or select enhanced persona)
        persona_name = session.get("persona")
        scam_already_detected = session.get("scam_detected", False)
        if not persona_name:
            scam_type = quick_scam_type(scammer_message)
            persona_name = _select_enhanced_persona(scam_type)

        # Use enhanced persona for prompt if available
        if persona_name in ENHANCED_PERSONAS:
            enhanced_persona = get_persona(persona_name)
            persona_prompt = enhanced_persona.get("enhanced_system_prompt", "")[:300]
        else:
            persona_prompt = self.persona_manager.get_persona_prompt(persona_name)

        # Build conversation context (last 3 messages only to save tokens)
        history = session.get("conversation_history", [])[-3:]
        history_text = _format_history(history) if history else "[First message]"

        # Determine stage from message count
        msg_count = session.get("message_count", 0)
        stage_tactic = get_stage_guidance(msg_count)
        context_hint = get_concise_context(session, msg_count)

        # Combined prompt - detection + extraction + response
        # Scammer psychology profiling (zero-cost, rule-based)
        profiler_output = self.scammer_profiler.analyze(
            session.get("conversation_history", [])
        )
        psychology_hint = self.scammer_profiler.get_prompt_modifier(profiler_output)

        # Proactive intel extraction hint
        extraction_hint = get_extraction_prompt_hint(session, profiler_output)

        prompt = f"""Analyze and respond. Output ONLY valid JSON.

MSG: "{scammer_message}"
HISTORY: {history_text}
PERSONA: {persona_prompt[:300]}
TACTIC: {stage_tactic}
{context_hint}
{psychology_hint}
{extraction_hint}

JSON output:
{{"is_scam":true/false,"confidence":0.0-1.0,"scam_type":"bank_fraud|upi_fraud|phishing|job_scam|lottery|investment|tech_support|other","intel":{{"bank_accounts":[],"upi_ids":[],"phone_numbers":[],"phishing_links":[],"email_addresses":[],"suspicious_keywords":[]}},"response":"victim reply 1-2 sentences"}}

SCAM SIGNS: urgency, threats, payment requests, OTP/KYC, prizes, job offers
EXTRACT: UPI IDs (x@bank), phones (10 digits), links (http), accounts (12+ digits), emails (x@domain.com), suspicious keywords (urgent, verify, blocked, prize, otp, kyc, etc.)
RESPONSE RULES:
- Sound like a REAL person, not an AI
- Use persona-appropriate language and imperfections
- Vary response style from previous messages
- Keep scammer engaged, extract their payment details"""

        try:
            response = await self.llm.generate_json(prompt=prompt, max_tokens=settings.MAX_TOKENS_JSON)
            result = json.loads(response)

            # Validate and normalize
            result = self._normalize_result(result, persona_name, msg_count, scammer_message)

            # Apply humanization if using enhanced persona
            if persona_name in ENHANCED_PERSONAS and result.get("response"):
                result["response"] = self.variation_engine.humanize_response(
                    base_response=result["response"],
                    persona_name=persona_name,
                    session_id=session_id,
                    message_number=msg_count
                )
                # Re-validate after humanization; replace fragment with fallback
                if not _is_valid_response(result["response"]):
                    result["response"] = self.variation_engine.get_fallback_response(
                        persona_name=persona_name,
                        conversation_stage=get_stage_guidance(msg_count)
                    )

            # Lock detection to session-level values after first detection
            if scam_already_detected:
                result["is_scam"] = True
                result["scam_type"] = session.get("scam_type", result["scam_type"])
                result["confidence"] = max(result.get("confidence", 0), session.get("scam_confidence", 0.7))
                result["persona"] = persona_name

            logger.info(
                f"Combined result: scam={result['is_scam']}, "
                f"type={result['scam_type']}, persona={persona_name}, "
                f"intel_count={_count_intel(result['intel'])}"
            )

            return result

        except Exception as e:
            logger.warning(f"Combined processing failed: {e}")
            return _fallback_response(scammer_message, persona_name, msg_count)

    def _normalize_result(self, result: Dict, persona: str, msg_count: int = 0, scammer_message: str = "") -> Dict:
        """Normalize and validate result. Replace fragment/short responses with fallback."""
        result.setdefault("is_scam", True)
        result.setdefault("confidence", 0.7)
        result.setdefault("scam_type", "other")
        result.setdefault("intel", {})
        result.setdefault("response", "I don't understand. Can you explain?")

        # If response is a JSON string, extract only the text response
        resp = result["response"]
        if isinstance(resp, str):
            stripped = resp.strip()
            if stripped.startswith("{") or stripped.startswith("["):
                try:
                    parsed = json.loads(stripped)
                    if isinstance(parsed, dict):
                        result["response"] = parsed.get("response", parsed.get("reply", str(parsed)))
                except (json.JSONDecodeError, ValueError):
                    pass
        elif isinstance(resp, dict):
            result["response"] = resp.get("response", resp.get("reply", str(resp)))

        # Replace truncated or fragment-like response with fallback
        if not _is_valid_response(result["response"]):
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
        intel.setdefault("email_addresses", [])
        intel.setdefault("suspicious_keywords", [])

        # Rename for compatibility
        if "phishing_links" not in intel and "links" in intel:
            intel["phishing_links"] = intel.pop("links")

        # Enhance with regex-based keyword extraction if not already populated
        if scammer_message and not intel.get("suspicious_keywords"):
            msg_lower = scammer_message.lower()
            keywords = [kw for kw in SCAM_KEYWORDS if kw in msg_lower]
            intel["suspicious_keywords"] = keywords[:5]  # Limit to 5 keywords

        result["persona"] = persona
        return result


# --- Module-level utility functions ---

def quick_scam_type(message: str) -> str:
    """Quick keyword-based scam type detection (no LLM)."""
    msg_lower = message.lower()
    for scam_type, keywords in SCAM_TYPE_KEYWORDS.items():
        if any(kw in msg_lower for kw in keywords):
            return scam_type
    return "other"


def _select_enhanced_persona(scam_type: str) -> str:
    """Select appropriate enhanced persona based on scam type."""
    candidates = PERSONA_MAPPING.get(scam_type, ["tech_naive_parent"])
    return random.choice(candidates)


def _format_history(history: List[Dict]) -> str:
    """Format history concisely."""
    return " | ".join(
        f"{m.get('sender', '?')[:1].upper()}: {m.get('text', '')[:50]}"
        for m in history
    )


def _is_valid_response(text: str) -> bool:
    """Return False if response looks truncated or fragment-only."""
    if not text or not isinstance(text, str):
        return False

    t = text.strip()
    if len(t) < MIN_RESPONSE_LEN:
        return False

    words = t.split()
    if len(words) <= 2:
        return False

    t_lower = t.lower()
    if t_lower in KNOWN_FRAGMENTS:
        return False

    return True


def _count_intel(intel: Dict) -> int:
    """Count total intelligence items."""
    return sum(len(v) for v in intel.values() if isinstance(v, list))


def _fallback_response(message: str, persona: str, msg_count: int) -> Dict:
    """Generate fallback result without LLM."""
    msg_lower = message.lower()

    # Check if scam using keywords
    matches = [kw for kw in SCAM_KEYWORDS if kw in msg_lower]
    is_scam = len(matches) >= 2

    # Extract intel with regex
    # Extract emails first for filtering
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', message)
    email_lower_set = {e.lower() for e in emails}
    intel = {
        "bank_accounts": re.findall(r'\b\d{10,18}\b', message),
        "upi_ids": [
            u for u in re.findall(r'[\w\.\-]+@[\w]+', message)
            if not any(d in u.lower() for d in ["gmail", "yahoo", "outlook", "com", "org", "net", "in"])
            and u.lower() not in email_lower_set
        ],
        "phone_numbers": re.findall(r'[6-9]\d{9}', message),
        "phishing_links": re.findall(r'https?://\S+', message),
        "email_addresses": emails,
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
        "scam_type": quick_scam_type(message),
        "intel": intel,
        "response": response,
        "persona": persona
    }
