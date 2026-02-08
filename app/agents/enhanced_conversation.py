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
    get_random_opening,
    should_add_typo
)
from app.agents.response_variation import ResponseVariationEngine
from app.agents.natural_flow import NaturalConversationFlow, get_stage_guidance
from app.agents.emotional_intelligence import EmotionalIntelligence
from app.agents.context_aware import ContextAwareManager, get_concise_context

logger = logging.getLogger(__name__)


class EnhancedConversationManager:
    """
    Orchestrates human-like conversation with scammers.
    Integrates persona, variation, emotion, and context components.
    """
    
    # Scam indicators for fallback detection
    SCAM_KEYWORDS = [
        "urgent", "blocked", "suspended", "verify", "account", "bank", "upi",
        "prize", "winner", "lottery", "claim", "fee", "payment", "otp", "kyc",
        "microsoft", "virus", "hacked", "job", "selected", "salary", "http"
    ]
    
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
        """
        Process scammer message with enhanced human-like response generation.
        
        Args:
            scammer_message: The scammer's message
            session: Current session state
            metadata: Optional request metadata
        
        Returns:
            Dict with: is_scam, scam_type, confidence, intelligence, response, persona
        """
        session_id = session.get("session_id", "unknown")
        
        # Get or select persona
        persona_name = session.get("persona")
        if not persona_name:
            scam_type = self._quick_scam_type(scammer_message)
            persona_name = self._select_enhanced_persona(scam_type)
        
        persona = get_persona(persona_name)
        
        # Get message number
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
            if not self._validate_response_quality(raw_response, persona_name):
                regen = await self._regenerate_response(persona_name, scammer_message, session, msg_count)
                raw_response = regen.strip().strip('"').strip("'")
            if not self._validate_response_quality(raw_response, persona_name):
                raw_response = self._get_contextual_fallback(persona_name, scammer_message, msg_count)
            raw_response = self._ensure_sentence_complete(raw_response)
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
            humanized = self._ensure_sentence_complete(humanized)
            if self.conversation_memory.is_too_similar(session_id, humanized):
                varied = await self._regenerate_with_variation(persona_name, scammer_message, session, msg_count)
                humanized = self._ensure_sentence_complete(varied.strip())
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
        
        # Get enhanced system prompt from persona
        system_prompt = persona.get("enhanced_system_prompt", "")
        
        # Get contextual instructions (keep concise for token limits)
        stage_guidance = get_stage_guidance(message_number)
        context_hint = get_concise_context(session, message_number)
        
        # Get emotional context
        emotion_context = self.emotion_layer.get_emotional_context(
            session_id=session_id,
            scammer_message=scammer_message,
            message_number=message_number,
            persona=persona
        )
        
        # Build conversation history (last 3 messages only to save tokens)
        history = session.get("conversation_history", [])[-3:]
        history_text = self._format_history(history) if history else "[First message]"
        
        # Build concise combined prompt
        prompt = f"""PERSONA INSTRUCTIONS:
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
        
        return prompt
    
    def _format_history(self, history: List[Dict]) -> str:
        """Format history concisely."""
        return " | ".join([
            f"{m.get('sender', '?')[:1].upper()}: {m.get('text', '')[:50]}"
            for m in history
        ])
    
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
    
    def _quick_scam_type(self, message: str) -> str:
        """Quick keyword-based scam type detection."""
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
    
    def _fallback_response(self, message: str, persona: str, msg_count: int) -> Dict:
        """Generate fallback result without LLM."""
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
        
        # Get natural fallback response
        response = self.variation_engine.get_fallback_response(
            persona_name=persona,
            conversation_stage=get_stage_guidance(msg_count)
        )
        
        return {
            "is_scam": is_scam,
            "confidence": min(len(matches) * 0.2, 0.9),
            "scam_type": self._quick_scam_type(message),
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
        if len(response) < 3:
            return False
        if len(response) > 300:
            return False
        if not self._is_sentence_complete(response):
            return False
        ai_patterns = [
            "i understand",
            "i see",
            "i apologize",
            "i'm an ai",
            "as an ai",
            "i cannot",
            "however,"
        ]
        lower = response.lower()
        if any(p in lower for p in ai_patterns):
            return False
        words = response.split()
        if len(words) != len(set(words)) and len(words) < 15:
            counts = {}
            for w in words:
                wl = w.lower()
                counts[wl] = counts.get(wl, 0) + 1
            if any(c >= 3 for c in counts.values()):
                return False
        return True

    def _is_sentence_complete(self, text: str) -> bool:
        """Check for obvious incomplete endings."""
        t = text.strip()
        if len(t.split()) <= 3:
            return bool(t) and t[-1] in ".!?"
        patterns = [
            r"\s+(I|Can|What|Why|How|When|Where|Who|Will|Should|Could|Would|Please|My|Your|The)$",
            r"\s+(is|are|was|were|be|been|has|have|had|do|does|did|will|would|should|could)$",
            r"\s+to$",
            r"\s+and$",
            r"\s+or$",
            r"\s+but$",
        ]
        for p in patterns:
            if re.search(p, t, re.IGNORECASE):
                return False
        return True

    def _ensure_sentence_complete(self, text: str) -> str:
        """Ensure ending punctuation and complete thought."""
        t = text.strip()
        if not t:
            return t
        if t[-1] in ".!?":
            return t
        if len(t.split()) <= 3:
            lw = t.lower()
            if lw in ["what", "why", "how", "when", "where", "who"]:
                return t + "?"
            return t + "."
        qs = ["what", "why", "how", "when", "where", "who", "can you", "could you", "should i"]
        if any(t.lower().startswith(q) for q in qs):
            return t + "?"
        return t + "."

    async def _regenerate_response(self, persona: str, scammer_message: str, session: Dict, msg_count: int) -> str:
        """Regenerate with stricter completion instruction."""
        prompt = self._build_enhanced_prompt(
            scammer_message=scammer_message,
            session=session,
            persona=get_persona(persona),
            message_number=msg_count
        ) + "\nEnsure the reply is a complete sentence ending with . ! or ?"
        try:
            txt = await self.llm.generate(
                prompt=prompt,
                temperature=0.5,
                max_tokens=200
            )
            return txt.strip()
        except Exception:
            return self._get_contextual_fallback(persona, scammer_message, msg_count)

    async def _regenerate_with_variation(self, persona: str, scammer_message: str, session: Dict, msg_count: int) -> str:
        """Regenerate emphasizing variation."""
        prompt = self._build_enhanced_prompt(
            scammer_message=scammer_message,
            session=session,
            persona=get_persona(persona),
            message_number=msg_count
        ) + "\nVary wording from previous messages. End with proper punctuation."
        try:
            txt = await self.llm.generate(
                prompt=prompt,
                temperature=0.6,
                max_tokens=200
            )
            return txt.strip()
        except Exception:
            return self._get_contextual_fallback(persona, scammer_message, msg_count)

    def _get_contextual_fallback(self, persona: str, scammer_message: str, message_number: int) -> str:
        """Contextual fallback based on scammer intent."""
        s = scammer_message.lower()
        if any(w in s for w in ["otp", "password", "pin", "cvv"]):
            options = {
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
        elif any(w in s for w in ["account", "number", "details"]):
            options = {
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
        elif any(w in s for w in ["send", "pay", "transfer", "upi"]):
            options = {
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
        else:
            options = {
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
        choices = options.get(persona, options["elderly_confused"])
        return random.choice(choices)

class ConversationMemory:
    """Track recent responses to avoid repetition."""
    def __init__(self):
        self.recent_responses = {}
    def is_too_similar(self, session_id: str, new_response: str) -> bool:
        if session_id not in self.recent_responses:
            self.recent_responses[session_id] = []
        recent = self.recent_responses[session_id]
        for old in recent[-3:]:
            s1 = set(old.lower().split())
            s2 = set(new_response.lower().split())
            if s1 and s2:
                inter = s1.intersection(s2)
                union = s1.union(s2)
                if len(inter) / len(union) > 0.7:
                    return True
        return False
    def add_response(self, session_id: str, response: str):
        if session_id not in self.recent_responses:
            self.recent_responses[session_id] = []
        self.recent_responses[session_id].append(response)
        if len(self.recent_responses[session_id]) > 5:
            self.recent_responses[session_id].pop(0)
