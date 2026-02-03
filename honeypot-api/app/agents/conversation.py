"""
Conversation Management System for AI Honeypot API.
Manages conversation stages and generates contextual victim responses.
"""

import logging
from typing import Dict, List
from enum import Enum

from app.core.llm import GroqClient
from app.agents.personas import PersonaManager

logger = logging.getLogger(__name__)


class ConversationStage(Enum):
    """Stages of a honeypot conversation."""
    INITIAL_HOOK = 1        # Scammer's opening (detect here)
    ENGAGEMENT = 2          # Build trust, show interest
    INFORMATION_PROBE = 3   # Scammer asks for details
    RESISTANCE = 4          # Show slight hesitation (seems human)
    GRADUAL_COMPLIANCE = 5  # Slowly give information
    INTELLIGENCE_MINING = 6 # Extract scammer's details
    PROLONGATION = 7        # Keep conversation going


class ConversationManager:
    """Manages conversation flow and generates victim responses."""
    
    # Stage-specific tactics for response generation
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
    
    def __init__(self, llm_client: GroqClient):
        self.llm = llm_client
        self.persona_manager = PersonaManager()
    
    def determine_stage(self, session: Dict) -> ConversationStage:
        """
        Determine conversation stage based on session state.
        
        Args:
            session: Current session dictionary
        
        Returns:
            Current conversation stage
        """
        msg_count = session.get("message_count", 0)
        has_intel = any(len(v) > 0 for v in session.get("intelligence", {}).values())
        
        if msg_count <= 2:
            return ConversationStage.INITIAL_HOOK
        elif msg_count <= 4:
            return ConversationStage.ENGAGEMENT
        elif msg_count <= 6:
            return ConversationStage.INFORMATION_PROBE
        elif msg_count <= 8:
            if not has_intel:
                return ConversationStage.RESISTANCE
            else:
                return ConversationStage.GRADUAL_COMPLIANCE
        elif msg_count <= 12:
            if has_intel:
                return ConversationStage.GRADUAL_COMPLIANCE
            else:
                return ConversationStage.INTELLIGENCE_MINING
        else:
            return ConversationStage.PROLONGATION
    
    async def generate_response(
        self,
        persona: str,
        scammer_message: str,
        conversation_history: List[Dict],
        stage: ConversationStage,
        current_intelligence: Dict
    ) -> str:
        """
        Generate a contextual victim response.
        
        Args:
            persona: Name of the persona to use
            scammer_message: Latest scammer message
            conversation_history: Recent conversation history
            stage: Current conversation stage
            current_intelligence: Already extracted intelligence
        
        Returns:
            Generated response text
        """
        # Get persona system prompt
        persona_prompt = self.persona_manager.get_persona_prompt(persona)
        
        # Get stage-specific tactics
        stage_tactics = self.STAGE_TACTICS.get(stage, "")
        
        # Build conversation context (last 5 messages)
        history_text = self._format_history(conversation_history[-5:])
        
        # Build intelligence context
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
                temperature=0.7,  # Creative but consistent
                max_tokens=100    # Keep responses short
            )
            
            # Clean response
            response = self._clean_response(response)
            
            # Validate response quality
            if not self._validate_response(response, persona):
                logger.warning(f"Response validation failed, using fallback")
                return self._fallback_response(stage, persona)
            
            logger.info(f"Generated response for stage {stage.name}: {response[:50]}...")
            return response
            
        except Exception as e:
            logger.error(f"Response generation failed: {str(e)}")
            return self._fallback_response(stage, persona)
    
    def _format_history(self, history: List[Dict]) -> str:
        """Format conversation history for prompt."""
        if not history:
            return "[No previous messages]"
        
        lines = []
        for msg in history:
            sender = msg.get("sender", "unknown").upper()
            text = msg.get("text", "")
            lines.append(f"{sender}: {text}")
        
        return "\n".join(lines)
    
    def _build_intel_context(self, intel: Dict) -> str:
        """Build context about extracted intelligence."""
        extracted = []
        for key, values in intel.items():
            if values:
                extracted.append(f"{key}: {len(values)} item(s)")
        
        if extracted:
            return f"""EXTRACTED SO FAR: {', '.join(extracted)}
Continue extracting more details. If they shared payment info, ask them to confirm it."""
        else:
            return """NO INTELLIGENCE YET: Focus on getting scammer to share their bank account, UPI ID, or links.
Ask where you should send money or what link to click."""
    
    def _clean_response(self, response: str) -> str:
        """Clean and normalize the response."""
        # Remove surrounding quotes
        response = response.strip().strip('"').strip("'")
        
        # Remove any assistant/AI prefixes
        prefixes_to_remove = [
            "As the victim,", "Response:", "Reply:", "Victim:", 
            "Me:", "User:", "Here's my response:"
        ]
        for prefix in prefixes_to_remove:
            if response.lower().startswith(prefix.lower()):
                response = response[len(prefix):].strip()
        
        return response.strip()
    
    def _validate_response(self, response: str, persona: str) -> bool:
        """Validate response quality."""
        # Check length
        if len(response) < 5 or len(response) > 300:
            return False
        
        # Check for AI language patterns
        ai_patterns = [
            "as an ai", "i'm an ai", "artificial intelligence",
            "language model", "i cannot", "i'm unable",
            "i apologize", "certainly!", "absolutely!",
            "here's", "sure thing"
        ]
        response_lower = response.lower()
        if any(pattern in response_lower for pattern in ai_patterns):
            return False
        
        return True
    
    def _fallback_response(self, stage: ConversationStage, persona: str) -> str:
        """Generate fallback response if LLM fails."""
        fallbacks = {
            ConversationStage.INITIAL_HOOK: "What happened? Why is my account blocked?",
            ConversationStage.ENGAGEMENT: "I see, that's concerning. What do I need to do?",
            ConversationStage.INFORMATION_PROBE: "Wait, before I share anything, can you verify yourself?",
            ConversationStage.RESISTANCE: "I'm not sure about this. Is it safe to share that?",
            ConversationStage.GRADUAL_COMPLIANCE: "Okay, I'll do it. Where should I send the money?",
            ConversationStage.INTELLIGENCE_MINING: "Send me the account number again, I didn't save it.",
            ConversationStage.PROLONGATION: "The link isn't working. Can you send it again?"
        }
        
        return fallbacks.get(stage, "I understand. What should I do next?")
