"""
Enhanced Conversation Manager for AI Honeypot.
Integrates all enhancement components for human-like responses.
"""

import json
import logging
import random
import re
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.llm import GroqClient

from app.agents.enhanced_personas import (
    ENHANCED_PERSONAS,
    get_persona,
)
from app.agents.response_variation import ResponseVariationEngine
from app.agents.natural_flow import NaturalConversationFlow, get_stage_guidance
from app.agents.emotional_intelligence import EmotionalIntelligence
from app.agents.context_aware import ContextAwareManager, get_concise_context
from app.agents.optimized import (
    quick_scam_type,
    SCAM_KEYWORDS,
    PERSONA_MAPPING,
    _format_history,
)
from app.agents.conversation import (
    is_sentence_complete,
    ensure_sentence_complete,
    AI_PATTERNS,
)

logger = logging.getLogger(__name__)


class ConversationMemory:
    """Track recent responses to avoid repetition."""

    SIMILARITY_THRESHOLD = 0.7
    MAX_HISTORY = 5

    def __init__(self):
        self.recent_responses: Dict[str, List[str]] = {}

    def is_too_similar(self, session_id: str, new_response: str) -> bool:
        """Check if new_response is too similar to recent responses."""
        recent = self.recent_responses.get(session_id, [])
        new_words = set(new_response.lower().split())

        if not new_words:
            return False

        for old in recent[-3:]:
            old_words = set(old.lower().split())
            if not old_words:
                continue
            intersection = new_words & old_words
            union = new_words | old_words
            if len(intersection) / len(union) > self.SIMILARITY_THRESHOLD:
                return True

        return False

    def add_response(self, session_id: str, response: str):
        """Record a response for similarity tracking."""
        if session_id not in self.recent_responses:
            self.recent_responses[session_id] = []
        self.recent_responses[session_id].append(response)
        if len(self.recent_responses[session_id]) > self.MAX_HISTORY:
            self.recent_responses[session_id].pop(0)


# Contextual fallback options organized by scammer intent and persona
CONTEXTUAL_FALLBACKS = {
    "otp_request": {
        "keywords": ["otp", "password", "pin", "cvv"],
        "responses": {
            "elderly_confused": [
                "I'm not sure what that is. Can you explain?",
                "My daughter usually helps me with these things.",
                "What do you mean by that?",
            ],
            "busy_professional": [
                "wait what",
                "which otp r u talking about",
                "didnt get any otp",
            ],
            "curious_student": [
                "what otp? i didnt get anything",
                "idk what ur talking about",
                "wait which one",
            ],
        }
    },
    "account_request": {
        "keywords": ["account", "number", "details"],
        "responses": {
            "elderly_confused": [
                "Which account number do you need?",
                "I have my passbook here, what should I tell you?",
                "Can you tell me why you need this?",
            ],
            "busy_professional": [
                "which account",
                "y do u need that",
                "send me ur details first",
            ],
            "curious_student": [
                "wait which account",
                "idk if i should share that tbh",
                "seems kinda sus ngl",
            ],
        }
    },
    "payment_request": {
        "keywords": ["send", "pay", "transfer", "upi"],
        "responses": {
            "elderly_confused": [
                "Where should I send it? What's your account?",
                "I don't know how to do that. Can you help?",
                "What details do I need to send money?",
            ],
            "busy_professional": [
                "send where",
                "whats the upi id again",
                "give me the details",
            ],
            "curious_student": [
                "wait send where exactly",
                "whats ur upi id",
                "ok but where do i send it",
            ],
        }
    },
    "generic": {
        "keywords": [],
        "responses": {
            "elderly_confused": [
                "I'm confused. Can you explain again?",
                "What do you mean?",
                "I don't understand.",
            ],
            "busy_professional": [
                "what",
                "didnt get that",
                "explain pls",
            ],
            "curious_student": [
                "wait what",
                "confused",
                "what r u saying",
            ],
        }
    }
}


class EnhancedConversationManager:
    """
    Orchestrates human-like conversation with scammers.
    Integrates persona, variation, emotion, and context components.
    """

    def __init__(self, llm_client: "GroqClient"):
        """Initialize with LLM client and all enhancement components."""
        self.llm = llm_client
        self.variation_engine = ResponseVariationEngine()
        self.flow_manager = NaturalConversationFlow()
        self.emotion_layer = EmotionalIntelligence()
        self.context_manager = ContextAwareManager()
        self.conversation_memory = ConversationMemory()

    async def process_message(
        self,
        scammer_message: str,
        session: Dict,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Process scammer message with enhanced human-like response generation."""
        session_id = session.get("session_id", "unknown")

        # Get or select persona
        persona_name = session.get("persona")
        if not persona_name:
            scam_type = quick_scam_type(scammer_message)
            persona_name = self._select_enhanced_persona(scam_type)

        persona = get_persona(persona_name)
        msg_count = session.get("message_count", 0) + 1

        # Build enhanced prompt
        prompt = self._build_enhanced_prompt(
            scammer_message=scammer_message,
            session=session,
            persona=persona,
            message_number=msg_count
        )

        try:
            response_text = await self.llm.generate_json(prompt=prompt, max_tokens=200)
            result = json.loads(response_text)
            result = self._normalize_result(result, persona_name)

            raw_response = result.get("response", "").strip().strip('"').strip("'")
            logger.info(f"Raw LLM output: '{raw_response}'")

            # Validate and regenerate if needed
            if not self._validate_response_quality(raw_response, persona_name):
                raw_response = await self._regenerate_response(
                    persona_name, scammer_message, session, msg_count
                )
                raw_response = raw_response.strip().strip('"').strip("'")

            if not self._validate_response_quality(raw_response, persona_name):
                raw_response = _get_contextual_fallback(
                    persona_name, scammer_message, msg_count
                )

            raw_response = ensure_sentence_complete(raw_response)

            # Humanize the response
            humanized = self.variation_engine.humanize_response(
                base_response=raw_response,
                persona_name=persona_name,
                session_id=session_id,
                message_number=msg_count
            ).strip()

            if not self.variation_engine.validate_human_likeness(humanized, persona_name):
                humanized = self.variation_engine.get_fallback_response(
                    persona_name=persona_name,
                    conversation_stage=get_stage_guidance(msg_count)
                )

            humanized = ensure_sentence_complete(humanized)

            # Check for repetition
            if self.conversation_memory.is_too_similar(session_id, humanized):
                varied = await self._regenerate_with_variation(
                    persona_name, scammer_message, session, msg_count
                )
                humanized = ensure_sentence_complete(varied.strip())

            self.conversation_memory.add_response(session_id, humanized)
            result["response"] = humanized

            logger.info(f"Final humanized response: '{humanized}'")
            logger.info(
                f"Enhanced result: scam={result['is_scam']}, "
                f"type={result['scam_type']}, persona={persona_name}, msg#{msg_count}"
            )
            return result

        except Exception as e:
            logger.warning(f"Enhanced processing failed: {e}")
            return self._fallback_response(scammer_message, persona_name, msg_count)

    def _build_enhanced_prompt(
        self,
        scammer_message: str,
        session: Dict,
        persona: Dict,
        message_number: int
    ) -> str:
        """Build enhanced prompt with all contextual layers."""
        session_id = session.get("session_id", "unknown")
        persona_name = persona.get("name", "tech_naive_parent")

        system_prompt = persona.get("enhanced_system_prompt", "")
        stage_guidance = get_stage_guidance(message_number)
        context_hint = get_concise_context(session, message_number)

        emotion_context = self.emotion_layer.get_emotional_context(
            session_id=session_id,
            scammer_message=scammer_message,
            message_number=message_number,
            persona=persona
        )

        history = session.get("conversation_history", [])[-3:]
        history_text = _format_history(history) if history else "[First message]"

        return f"""PERSONA INSTRUCTIONS:
{system_prompt[:500]}

{context_hint}

EMOTIONAL CONTEXT:
{emotion_context[:300]}

---
SCAMMER MESSAGE: "{scammer_message}"
RECENT HISTORY: {history_text}
MESSAGE NUMBER: {message_number}
STAGE TACTIC: {stage_guidance}

OUTPUT FORMAT - Respond with ONLY valid JSON:
{{"is_scam":true/false,"confidence":0.0-1.0,"scam_type":"bank_fraud|upi_fraud|phishing|job_scam|lottery|investment|tech_support|other","intel":{{"bank_accounts":[],"upi_ids":[],"phone_numbers":[],"links":[]}},"response":"victim reply 1-2 sentences"}}

EXTRACTION RULES:
- UPI IDs: x@bank format
- Phone numbers: 10 digits starting with 6-9
- Bank accounts: 12+ digit numbers
- Links: any http/https URLs

RESPONSE RULES:
- Sound like a REAL PERSON, not an AI
- Vary your response from previous ones
- Stay in character as described in persona
- Keep scammer engaged, ask for THEIR details/payment info"""

    def _select_enhanced_persona(self, scam_type: str) -> str:
        """Select appropriate enhanced persona based on scam type."""
        candidates = PERSONA_MAPPING.get(scam_type, ["tech_naive_parent"])
        return random.choice(candidates)

    def _normalize_result(self, result: Dict, persona: str) -> Dict:
        """Normalize and validate result."""
        result.setdefault("is_scam", True)
        result.setdefault("confidence", 0.7)
        result.setdefault("scam_type", "other")
        result.setdefault("intel", {})
        result.setdefault("response", "I don't understand. Can you explain?")

        intel = result["intel"]
        intel.setdefault("bank_accounts", [])
        intel.setdefault("upi_ids", [])
        intel.setdefault("phone_numbers", [])
        intel.setdefault("links", [])
        intel.setdefault("suspicious_keywords", [])

        if "phishing_links" not in intel and "links" in intel:
            intel["phishing_links"] = intel.pop("links")

        result["persona"] = persona
        return result

    def _fallback_response(self, message: str, persona: str, msg_count: int) -> Dict:
        """Generate fallback result without LLM."""
        msg_lower = message.lower()
        matches = [kw for kw in SCAM_KEYWORDS if kw in msg_lower]
        is_scam = len(matches) >= 2

        intel = {
            "bank_accounts": re.findall(r'\b\d{10,18}\b', message),
            "upi_ids": [
                u for u in re.findall(r'[\w\.\-]+@[\w]+', message)
                if not any(d in u.lower() for d in ["gmail", "yahoo", "outlook"])
            ],
            "phone_numbers": re.findall(r'[6-9]\d{9}', message),
            "phishing_links": re.findall(r'https?://\S+', message),
            "suspicious_keywords": matches[:5]
        }

        response = self.variation_engine.get_fallback_response(
            persona_name=persona,
            conversation_stage=get_stage_guidance(msg_count)
        )

        return {
            "is_scam": is_scam,
            "confidence": min(len(matches) * 0.2, 0.9),
            "scam_type": quick_scam_type(message),
            "intel": intel,
            "response": response,
            "persona": persona
        }

    def clear_session(self, session_id: str):
        """Clear session data from components."""
        self.emotion_layer.clear_session(session_id)
        if session_id in self.variation_engine.message_count:
            del self.variation_engine.message_count[session_id]

    def _validate_response_quality(self, response: str, persona: str) -> bool:
        """Comprehensive response validation."""
        if len(response) < 3 or len(response) > 300:
            return False

        if not is_sentence_complete(response):
            return False

        lower = response.lower()
        if any(p in lower for p in AI_PATTERNS):
            return False

        # Check for excessive word repetition
        words = response.split()
        if len(words) < 15:
            counts: Dict[str, int] = {}
            for w in words:
                wl = w.lower()
                counts[wl] = counts.get(wl, 0) + 1
            if any(c >= 3 for c in counts.values()):
                return False

        return True

    async def _regenerate_response(
        self, persona: str, scammer_message: str, session: Dict, msg_count: int
    ) -> str:
        """Regenerate with stricter completion instruction."""
        prompt = self._build_enhanced_prompt(
            scammer_message=scammer_message,
            session=session,
            persona=get_persona(persona),
            message_number=msg_count
        ) + "\nEnsure the reply is a complete sentence ending with . ! or ?"

        try:
            txt = await self.llm.generate(prompt=prompt, temperature=0.5, max_tokens=200)
            return txt.strip()
        except Exception:
            return _get_contextual_fallback(persona, scammer_message, msg_count)

    async def _regenerate_with_variation(
        self, persona: str, scammer_message: str, session: Dict, msg_count: int
    ) -> str:
        """Regenerate emphasizing variation."""
        prompt = self._build_enhanced_prompt(
            scammer_message=scammer_message,
            session=session,
            persona=get_persona(persona),
            message_number=msg_count
        ) + "\nVary wording from previous messages. End with proper punctuation."

        try:
            txt = await self.llm.generate(prompt=prompt, temperature=0.6, max_tokens=200)
            return txt.strip()
        except Exception:
            return _get_contextual_fallback(persona, scammer_message, msg_count)


def _get_contextual_fallback(
    persona: str, scammer_message: str, message_number: int
) -> str:
    """Contextual fallback based on scammer intent."""
    s = scammer_message.lower()

    # Find matching fallback category
    for category_key, category in CONTEXTUAL_FALLBACKS.items():
        if category_key == "generic":
            continue
        if any(w in s for w in category["keywords"]):
            choices = category["responses"].get(
                persona, category["responses"].get("elderly_confused", [])
            )
            return random.choice(choices) if choices else "I don't understand."

    # Default to generic fallback
    generic = CONTEXTUAL_FALLBACKS["generic"]["responses"]
    choices = generic.get(persona, generic.get("elderly_confused", []))
    return random.choice(choices) if choices else "I don't understand."
