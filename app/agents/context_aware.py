"""
Context-Aware Manager for AI Honeypot.
Provides rich contextual layers for natural conversation adaptations.
"""

import random
import datetime
from typing import Dict, List
from app.core.config import settings
from app.agents.extraction_strategies import get_guided_tactic

# Time-of-day context descriptions
TIME_CONTEXTS = [
    (6, 9, "Morning: You might be getting ready for work, distracted. Could mention 'getting ready', 'running late'."),
    (9, 12, "Late morning: Likely at work/busy. Brief responses likely."),
    (12, 14, "Lunch time: Might be free to respond more."),
    (14, 18, "Afternoon: Still working, potentially rushed."),
    (18, 22, "Evening: More relaxed, can be more detailed."),
]
DEFAULT_TIME_CONTEXT = "Late night: Brief responses, tired, maybe typos from fatigue."

# Natural behavior hints for conversation realism
NATURAL_BEHAVIORS = [
    "Real people sometimes misread messages - you can respond to the wrong part",
    "Real people sometimes forget what was said 3 messages ago - you can ask again",
    "Real people get tired in long conversations - show fatigue after 10+ messages",
    "Real people correct themselves: 'wait no I mean...'",
    "Real people sometimes go slightly off-topic then return",
    "Real people pause mid-thought: 'I'm just... I don't know...'",
    "Real people sometimes don't finish their sentences when",
    "Real people ask the same question in different words if still confused",
]

# Persona-specific conversation hints
PERSONA_HINTS = {
    "elderly_confused": [
        "You might mention needing to find your reading glasses",
        "You might say you need to ask your grandchild first",
        "You might worry about 'doing it wrong'"
    ],
    "busy_professional": [
        "You might say 'hold on, call coming in'",
        "You might respond 'sorry was afk' after a delay",
        "You might make autocorrect errors from fast typing"
    ],
    "curious_student": [
        "You might suddenly question if this is a scam (then be convinced it's not)",
        "You might mention a friend had something similar happen",
        "You might use slang inconsistently"
    ],
    "tech_naive_parent": [
        "You might ask if you should call your son/daughter first",
        "You might compare this to going to a physical bank",
        "You might worry about getting hacked"
    ],
    "desperate_job_seeker": [
        "You might mention how long you've been searching",
        "You might express anxiety about missing this opportunity",
        "You might over-share your qualifications"
    ]
}


class ContextAwareManager:
    """Manages context-specific response adaptations."""

    def enhance_prompt_with_context(
        self,
        base_prompt: str,
        session: Dict,
        scammer_message: str,
        persona: Dict,
        message_number: int
    ) -> str:
        """Add rich contextual layers to prompt."""
        context_layers = [
            self._get_time_context(),
            self._get_scammer_pattern_context(session),
            self._get_extraction_strategy(session, message_number),
            self._get_natural_conversation_hints(message_number, persona),
            _ANTI_DETECTION_GUIDANCE,
        ]

        return f"""{base_prompt}

========================
CONTEXTUAL ENHANCEMENTS
========================

{chr(10).join(context_layers)}

FINAL INSTRUCTION:
Generate a response that sounds like a REAL person typed it on their phone, not an AI.
Vary from your previous messages. Be natural. Be human. Be imperfect.
"""

    def _get_time_context(self) -> str:
        """Add time-of-day realism."""
        hour = datetime.datetime.now().hour

        for start, end, description in TIME_CONTEXTS:
            if start <= hour < end:
                return f"TIME CONTEXT:\n- {description}"

        return f"TIME CONTEXT:\n- {DEFAULT_TIME_CONTEXT}"

    def _get_scammer_pattern_context(self, session: Dict) -> str:
        """Analyze scammer's pattern and adapt."""
        history = session.get("conversation_history", [])
        scammer_msgs = [msg for msg in history if msg.get("sender") == "scammer"]

        if len(scammer_msgs) < 2:
            return "SCAMMER PATTERN: Too early to detect pattern"

        avg_length = sum(
            len(msg.get("text", "").split()) for msg in scammer_msgs
        ) / len(scammer_msgs)

        uses_formal = any(
            "sir" in msg.get("text", "").lower() or "madam" in msg.get("text", "").lower()
            for msg in scammer_msgs
        )

        context = "SCAMMER PATTERN DETECTED:\n"
        if avg_length > 15:
            context += "- They write long messages → You can write longer responses to match\n"
        else:
            context += "- They write short messages → Keep your responses brief too\n"

        if uses_formal:
            context += "- They're formal → Match with slightly formal language (if fits persona)\n"
        else:
            context += "- They're casual → You can be more casual\n"

        return context

    def _get_extraction_strategy(self, session: Dict, message_number: int) -> str:
        """Strategic guidance on extracting intelligence."""
        intel = session.get("intelligence", {})
        has_bank = len(intel.get("bank_accounts", [])) > 0
        has_upi = len(intel.get("upi_ids", [])) > 0
        has_link = len(intel.get("phishing_links", [])) > 0

        strategy = "INTELLIGENCE EXTRACTION STRATEGY:\n"

        if message_number <= 3:
            strategy += "- Too early to directly ask for their details\n"
            strategy += "- Focus on building trust and understanding the situation\n"
        elif message_number <= 6:
            strategy += "- Good time to start asking questions that reveal their details\n"
            strategy += "- Ask: 'Where should I send it?', 'What's the account?', 'Can you send the link?'\n"
        else:
            if not has_upi and not has_bank:
                strategy += "- PRIORITY: Get payment details (UPI ID or bank account)\n"
                strategy += "- Be direct: 'What's the UPI ID again?', 'Send me the account number'\n"
            if not has_link:
                strategy += "- Try to get them to share links if they mention verification/website\n"
            if has_upi or has_bank:
                strategy += "- ✓ Payment details extracted\n"
                strategy += "- Can ask for 'backup method' or 'alternative account' for more intel\n"

        return strategy

    def _get_natural_conversation_hints(self, message_number: int, persona: Dict) -> str:
        """Hints for natural conversation flow."""
        selected_hints = random.sample(NATURAL_BEHAVIORS, min(3, len(NATURAL_BEHAVIORS)))

        hints = "NATURAL CONVERSATION HINTS:\n"
        for hint in selected_hints:
            hints += f"- {hint}\n"

        persona_name = persona.get("name", "")
        if persona_name in PERSONA_HINTS:
            persona_hint = random.choice(PERSONA_HINTS[persona_name])
            hints += f"- PERSONA-SPECIFIC: {persona_hint}\n"

        return hints


# Anti-detection guidance (constant, no need to regenerate)
_ANTI_DETECTION_GUIDANCE = """ANTI-DETECTION MEASURES:

CRITICAL - Avoid these honeypot tells:
✗ Being TOO eager to get their details (suspicious)
✗ Perfect grammar and spelling (robotic)
✗ Responding instantly every time (bot-like)
✗ Never making mistakes or needing clarification (unrealistic)
✗ Asking in a pattern: first this, then that (predictable)
✗ Being overly compliant without ANY hesitation (obvious trap)

✓ Instead:
✓ Show natural hesitation before complying
✓ Make them convince you over several messages
✓ Ask genuine-sounding questions about safety
✓ Occasionally misunderstand something they said
✓ Vary your response style - don't be predictable
✓ Show emotions that real victims would feel

Remember: Real scam victims are confused, worried, and skeptical before they trust.
Build that trust gradually. Don't rush the intelligence extraction."""


def get_concise_context(session: Dict, message_number: int) -> str:
    """Get concise stage context with optional guided extraction tactic."""
    intel = session.get("intelligence", {})
    has_intel = any(len(v) > 0 for v in intel.values())

    if message_number <= 3:
        base = "STAGE: Initial - show confusion/concern, don't ask for details yet"
    elif message_number <= 6:
        base = "STAGE: Understanding - ask clarifying questions, start probing for their details"
    elif message_number <= 10:
        if has_intel:
            base = "STAGE: Complying - confirm their details, ask for clarification"
        else:
            base = "STAGE: Extracting - directly ask for their payment details/links"
    else:
        base = "STAGE: Prolonging - report issues, ask for alternative methods"

    if settings.EXTRACTION_ENABLED:
        guided_text, tactic_id = get_guided_tactic(
            session, message_number, session.get("persona")
        )
        if guided_text:
            strategy_state = session.get("strategy_state") or {}
            strategy_state["last_tactic"] = {
                "tactic_id": tactic_id,
                "text": guided_text,
                "msg": message_number,
                "scam_type": session.get("scam_type")
            }
            session["strategy_state"] = strategy_state
            return f"{base} | GUIDED: {guided_text}"

    return base
