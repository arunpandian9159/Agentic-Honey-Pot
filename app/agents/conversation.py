"""
Conversation Management System for AI Honeypot API.
Manages conversation stages and generates contextual victim responses.
"""

import re
import logging
from typing import Dict, List, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from app.core.llm import GroqClient

from app.agents.personas import PersonaManager

logger = logging.getLogger(__name__)

# Patterns that indicate an incomplete sentence ending
INCOMPLETE_ENDING_PATTERNS = [
    r"\s+(I|Can|What|Why|How|When|Where|Who|Will|Should|Could|Would|Please|My|Your|The)$",
    r"\s+(is|are|was|were|be|been|has|have|had|do|does|did|will|would|should|could)$",
    r"\s+(to|and|or|but)$",
]

# Question-starting words/phrases
QUESTION_STARTERS = [
    "what", "why", "how", "when", "where", "who",
    "can you", "could you", "should i"
]

# AI-like patterns that should not appear in victim responses
AI_PATTERNS = [
    "as an ai", "i'm an ai", "artificial intelligence",
    "language model", "i cannot", "i'm unable",
    "i apologize", "certainly!", "absolutely!",
    "here's", "sure thing"
]


class ConversationStage(Enum):
    """Stages of a honeypot conversation."""
    INITIAL_HOOK = 1
    ENGAGEMENT = 2
    INFORMATION_PROBE = 3
    RESISTANCE = 4
    GRADUAL_COMPLIANCE = 5
    INTELLIGENCE_MINING = 6
    PROLONGATION = 7


class ConversationManager:
    """Manages conversation flow and generates victim responses."""

    STAGE_TACTICS = {
        ConversationStage.INITIAL_HOOK: """
TACTICS: Show concern and ask why. Express worry but don't comply immediately.
- Ask what happened and why
- Show concern about the situation
- Don't give any information yet
Example: "What? Why is my account blocked? What happened?"
""",
        ConversationStage.ENGAGEMENT: """
TACTICS: Build trust, ask questions, show you're taking this seriously.
- Express willingness to help resolve the issue
- Ask for more details about the problem
- Show you trust them but need clarity
Example: "I see, that sounds serious. What do I need to do to fix this?"
""",
        ConversationStage.INFORMATION_PROBE: """
TACTICS: Scammer will ask for your info. Show slight hesitation, ask for their details first.
- Express some caution
- Ask them to verify their identity
- Request their contact details or ID
Example: "Before I share anything, can you confirm you're from the bank? What's your employee ID?"
""",
        ConversationStage.RESISTANCE: """
TACTICS: Show natural caution. Ask to verify through official channels.
- Express doubt politely
- Mention wanting to verify independently
- Don't refuse entirely, just hesitate
Example: "I'm not sure about sharing that. Can I call the bank directly instead?"
""",
        ConversationStage.GRADUAL_COMPLIANCE: """
TACTICS: Slowly give in, but keep asking for their details too.
- Agree to help but ask for their payment details
- Request the account number, UPI ID, or link they want you to use
- Seem like you're preparing to comply
Example: "Okay, I trust you. But where should I send the payment? What's the account number?"
""",
        ConversationStage.INTELLIGENCE_MINING: """
TACTICS: Actively extract scammer's details. Ask for payment methods, links, contact info.
- Request payment details directly
- Ask them to resend links or account numbers
- Pretend you're ready to act
Example: "I'll do it right now. Send me the UPI ID again? And the link you mentioned?"
""",
        ConversationStage.PROLONGATION: """
TACTICS: Keep conversation alive. Report small technical issues, ask for clarification.
- Say you're having trouble with their link
- Ask for alternative payment methods
- Report errors and request help
Example: "The link isn't working. Can you send another one? Or should I try a different payment method?"
"""
    }

    FALLBACK_RESPONSES = {
        ConversationStage.INITIAL_HOOK: "What happened? Why is my account blocked?",
        ConversationStage.ENGAGEMENT: "I see, that's concerning. What do I need to do?",
        ConversationStage.INFORMATION_PROBE: "Wait, before I share anything, can you verify yourself?",
        ConversationStage.RESISTANCE: "I'm not sure about this. Is it safe to share that?",
        ConversationStage.GRADUAL_COMPLIANCE: "Okay, I'll do it. Where should I send the money?",
        ConversationStage.INTELLIGENCE_MINING: "Send me the account number again, I didn't save it.",
        ConversationStage.PROLONGATION: "The link isn't working. Can you send it again?"
    }

    # Prefixes that LLM sometimes adds to responses
    RESPONSE_PREFIXES = [
        "As the victim,", "Response:", "Reply:", "Victim:",
        "Me:", "User:", "Here's my response:"
    ]

    def __init__(self, llm_client: "GroqClient"):
        self.llm = llm_client
        self.persona_manager = PersonaManager()

    def determine_stage(self, session: Dict) -> ConversationStage:
        """Determine conversation stage based on session state."""
        msg_count = session.get("message_count", 0)
        has_intel = any(
            len(v) > 0 for v in session.get("intelligence", {}).values()
        )

        if msg_count <= 2:
            return ConversationStage.INITIAL_HOOK
        if msg_count <= 4:
            return ConversationStage.ENGAGEMENT
        if msg_count <= 6:
            return ConversationStage.INFORMATION_PROBE
        if msg_count <= 8:
            if has_intel:
                return ConversationStage.GRADUAL_COMPLIANCE
            return ConversationStage.RESISTANCE
        if msg_count <= 12:
            if has_intel:
                return ConversationStage.GRADUAL_COMPLIANCE
            return ConversationStage.INTELLIGENCE_MINING
        return ConversationStage.PROLONGATION

    async def generate_response(
        self,
        persona: str,
        scammer_message: str,
        conversation_history: List[Dict],
        stage: ConversationStage,
        current_intelligence: Dict
    ) -> str:
        """Generate a contextual victim response."""
        persona_prompt = self.persona_manager.get_persona_prompt(persona)
        stage_tactics = self.STAGE_TACTICS.get(stage, "")
        history_text = self._format_history(conversation_history[-5:])
        intel_context = self._build_intel_context(current_intelligence)

        full_prompt = f"""{persona_prompt}

CONVERSATION SO FAR:
{history_text}

LATEST SCAMMER MESSAGE:
"{scammer_message}"

CURRENT STAGE: {stage.name}
{stage_tactics}

{intel_context}

YOUR OBJECTIVES (in order of priority):
1. Stay in character - be natural and believable as the persona
2. Keep scammer engaged - show interest, don't end the conversation
3. Extract information - get bank accounts, UPI IDs, links from them
4. Don't seem suspicious - avoid being too eager or too resistant

IMPORTANT RULES:
- Keep response 1-3 sentences (natural SMS/chat length)
- Show appropriate emotion (worry, curiosity, confusion based on your persona)
- Ask questions that prompt scammer to share their payment details
- Mirror scammer's urgency but add slight hesitation
- If scammer shares payment details, ask clarifying questions about them
- Never break character or reveal you are an AI
- Use language style matching your persona

Generate ONLY the victim's reply. No explanations, no quotes around the response, just the message text.
"""

        try:
            response = await self.llm.generate(
                prompt=full_prompt,
                temperature=0.7,
                max_tokens=200
            )

            response = self._clean_response(response)
            response = ensure_sentence_complete(response)

            if not self._validate_response(response):
                logger.warning("Response validation failed, using fallback")
                return self._fallback_response(stage)

            logger.info(f"Generated response for stage {stage.name}: {response[:50]}...")
            return response

        except Exception as e:
            logger.error(f"Response generation failed: {str(e)}")
            return self._fallback_response(stage)

    def _format_history(self, history: List[Dict]) -> str:
        """Format conversation history for prompt."""
        if not history:
            return "[No previous messages]"

        return "\n".join(
            f"{msg.get('sender', 'unknown').upper()}: {msg.get('text', '')}"
            for msg in history
        )

    def _build_intel_context(self, intel: Dict) -> str:
        """Build context about extracted intelligence."""
        extracted = [
            f"{key}: {len(values)} item(s)"
            for key, values in intel.items()
            if values
        ]

        if extracted:
            return (
                f"EXTRACTED SO FAR: {', '.join(extracted)}\n"
                "Continue extracting more details. If they shared payment info, ask them to confirm it."
            )
        return (
            "NO INTELLIGENCE YET: Focus on getting scammer to share their bank account, UPI ID, or links.\n"
            "Ask where you should send money or what link to click."
        )

    def _clean_response(self, response: str) -> str:
        """Clean and normalize the response."""
        response = response.strip().strip('"').strip("'")

        for prefix in self.RESPONSE_PREFIXES:
            if response.lower().startswith(prefix.lower()):
                response = response[len(prefix):].strip()

        return response.strip()

    def _validate_response(self, response: str) -> bool:
        """Validate response quality."""
        if len(response) < 5 or len(response) > 300:
            return False

        response_lower = response.lower()
        if any(pattern in response_lower for pattern in AI_PATTERNS):
            return False

        if len(response) > 20 and response[-1] not in ".!?":
            return False

        if not is_sentence_complete(response):
            return False

        return True

    def _fallback_response(self, stage: ConversationStage) -> str:
        """Generate fallback response if LLM fails."""
        return self.FALLBACK_RESPONSES.get(stage, "I understand. What should I do next?")


def is_sentence_complete(text: str) -> bool:
    """Check if text ends with a complete thought."""
    t = text.strip()
    if not t:
        return False

    if len(t.split()) <= 3:
        return t[-1] in ".!?"

    for pattern in INCOMPLETE_ENDING_PATTERNS:
        if re.search(pattern, t, re.IGNORECASE):
            return False

    return True


def ensure_sentence_complete(text: str) -> str:
    """Ensure text ends with proper punctuation."""
    t = text.strip()
    if not t:
        return t

    if t[-1] in ".!?":
        return t

    # Single-word or very short responses
    if len(t.split()) <= 3:
        if t.lower() in QUESTION_STARTERS[:6]:
            return t + "?"
        return t + "."

    # Multi-word: check if it starts like a question
    if any(t.lower().startswith(q) for q in QUESTION_STARTERS):
        return t + "?"

    return t + "."
