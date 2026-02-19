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

# Scam indicators for fallback detection (expanded for deeper red-flag coverage)
SCAM_KEYWORDS = [
    "urgent", "blocked", "suspended", "verify", "account", "bank", "upi",
    "prize", "winner", "lottery", "claim", "fee", "payment", "otp", "kyc",
    "microsoft", "virus", "hacked", "job", "selected", "salary", "http",
    "freeze", "aadhar", "pan", "cvv", "pin", "insurance", "refund",
    "cashback", "loan", "emi", "reward", "offer", "free", "guarantee",
    "processing", "registration", "investigation", "legal action",
    "police", "arrest", "warrant", "deadline", "expire", "deactivate",
    "compromise", "unauthorized", "suspicious", "immediately",
]

# Scam type detection keywords (expanded with India-specific terms)
SCAM_TYPE_KEYWORDS = {
    "bank_fraud": [
        "bank", "account", "kyc", "sbi", "hdfc", "icici", "axis",
        "blocked", "suspended", "freeze", "deactivate", "neft",
        "rtgs", "ifsc", "aadhar", "pan", "cvv",
    ],
    "upi_fraud": [
        "upi", "@", "paytm", "phonepe", "googlepay", "gpay",
        "refund", "collect request", "payment failed", "cashback",
    ],
    "phishing": ["http", "link", "click", "www", "verify", "login", "update"],
    "job_scam": [
        "job", "selected", "salary", "hiring", "work from home",
        "registration fee", "training fee", "placement",
    ],
    "lottery": ["prize", "winner", "lottery", "won", "lucky draw", "reward", "congratulations"],
    "investment": [
        "invest", "return", "profit", "double", "trading",
        "crypto", "forex", "guaranteed return", "mutual fund",
    ],
    "tech_support": [
        "virus", "microsoft", "hacked", "apple", "tech support",
        "remote access", "anydesk", "teamviewer", "compromised",
    ],
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

        # Determine stage from message count
        msg_count = session.get("message_count", 0)
        stage_tactic = get_stage_guidance(msg_count)
        context_hint = get_concise_context(session, msg_count)

        # Ultra-compact prompt — detection + extraction + response in minimal tokens
        prompt = f"""JSON only. Scam honeypot: detect, extract intel, reply in-character.
        MSG:"{scammer_message}"
        ROLE:{persona_prompt[:150]}
        STAGE:{stage_tactic}
        {context_hint}
        {{"is_scam":bool,"confidence":0-1,"scam_type":"bank_fraud|upi_fraud|phishing|job_scam|lottery|investment|tech_support|other","intel":{{"upi_ids":[],"phone_numbers":[],"phishing_links":[],"bank_accounts":[],"email_addresses":[],"suspicious_keywords":[]}},"response":"1-2 sentence victim reply, probe for their details"}}"""

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

        except json.JSONDecodeError as e:
            logger.warning(f"LLM returned invalid JSON, using fallback: {e}")
            return _fallback_response(scammer_message, persona_name, msg_count)
        except Exception as e:
            logger.error(f"Agent processing failed ({type(e).__name__}): {e}")
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
    """Generate fallback result without LLM. Uses probing questions to elicit intel."""
    msg_lower = message.lower()

    # Check if scam using keywords (lowered threshold — 1 keyword is enough)
    matches = [kw for kw in SCAM_KEYWORDS if kw in msg_lower]
    is_scam = len(matches) >= 1

    # Extract intel with improved regex patterns
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', message)
    email_lower_set = {e.lower() for e in emails}

    # UPI IDs: word@bankcode but exclude obvious email domains
    email_domains = {"gmail", "yahoo", "outlook", "hotmail", "protonmail", "com", "org", "net", "io", "co"}
    upi_candidates = re.findall(r'[\w\.\-]+@[\w]+', message)
    upi_ids = [
        u for u in upi_candidates
        if not any(d in u.lower().split("@")[-1] for d in email_domains)
        and u.lower() not in email_lower_set
    ]

    # Phone numbers: handle +91, country codes, dashes, spaces - preserve original format
    phone_patterns_raw = (
        re.findall(r'\+91[\s\-]?\d{10}', message)
        + re.findall(r'\+91[\s\-]?[6-9]\d{9}', message)
        + re.findall(r'(?<!\d)[6-9]\d{9}(?!\d)', message)
    )
    phones = []
    for p in phone_patterns_raw:
        cleaned = p.strip()
        phones.append(cleaned)
        digits_only = re.sub(r'[\s\-\+]', '', cleaned)[-10:]
        if digits_only != cleaned:
            phones.append(digits_only)
    phones = list(set(phones))

    # Bank accounts: 9 to 18 digits
    bank_accounts = re.findall(r'\b\d{9,18}\b', message)

    # IFSC codes
    ifsc_codes = re.findall(r'\b[A-Z]{4}0[A-Z0-9]{6}\b', message)

    intel = {
        "bank_accounts": bank_accounts + ifsc_codes,
        "upi_ids": upi_ids,
        "phone_numbers": phones,
        "phishing_links": re.findall(r'https?://\S+', message),
        "email_addresses": emails,
        "suspicious_keywords": matches[:8]
    }

    # Fallback responses by stage — multiple probing variants per stage
    stage_responses = {
        "early": [
            "What happened? Why is my account blocked? Can you tell me which account?",
            "Oh no this is scary. Who are you calling from? What is your name?",
            "What??? My account is blocked?? But I used it yesterday. Which branch are you from?",
            "I'm confused. What do I need to do? Can you explain slowly please?",
        ],
        "mid_probe": [
            "I see that its serious. Where exactly should I send this? What's the account number?",
            "OK I want to fix this. Can you give me your phone number so I can call you back?",
            "My son told me to ask for your employee ID before I do anything. What is it?",
            "I'll do what you say but first, which bank should I transfer to? And what's the IFSC?",
        ],
        "mid_verify": [
            "Before I do anything, can you verify who you are? What's your official ID?",
            "Wait, can you tell me your department name and employee number please?",
            "I need to check with my family first. Can you send me the link again so I can show them?",
            "My neighbor says I should verify. Can you give me an official number to call back?",
        ],
        "late_extract": [
            "Okay I'll do it. Where should I send the payment? What UPI ID should I use?",
            "Fine fine I'll cooperate. Just tell me the account number and IFSC code.",
            "OK I'm at the bank now. They're asking for the beneficiary account number. What is it?",
            "Alright I'll send it. What's the exact UPI ID? And how much exactly?",
        ],
        "final": [
            "The link isn't working. Can you send it again? My phone is slow.",
            "I tried but it's showing error. Can you give me another link or number?",
            "It's not going through. Is there another UPI ID I can try?",
            "My phone froze. Can you resend everything — the link and your number?",
        ],
    }

    if msg_count <= 2:
        response = random.choice(stage_responses["early"])
    elif msg_count <= 5:
        response = random.choice(stage_responses["mid_probe"])
    elif msg_count <= 8:
        response = random.choice(stage_responses["mid_verify"])
    elif msg_count <= 12:
        response = random.choice(stage_responses["late_extract"])
    else:
        response = random.choice(stage_responses["final"])

    return {
        "is_scam": is_scam,
        "confidence": min(len(matches) * 0.15 + 0.3, 0.95) if is_scam else 0.0,
        "scam_type": quick_scam_type(message),
        "intel": intel,
        "response": response,
        "persona": persona
    }
