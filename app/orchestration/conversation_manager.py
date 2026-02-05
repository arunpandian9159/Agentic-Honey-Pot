"""
Conversation Manager for AI Honeypot API.
Orchestrates the conversation flow, persona selection, and response generation.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.agents.base_agent import AgentInterface
from app.agents.personas.base_persona import BasePersona
from app.agents.personas.manager import PersonaManager
from app.agents.humanization.variation_engine import VariationEngine
from app.agents.humanization.emotional_intelligence import EmotionalIntelligence
from app.agents.humanization.context_aware import ContextAwareManager
from app.agents.humanization.natural_flow import NaturalConversationFlow
from app.detection.detector import ScamDetector
from app.detection.models.detection_result import DetectionResult
from app.intelligence.extractor import IntelligenceExtractor
from app.intelligence.models.intelligence_data import IntelligenceData

logger = logging.getLogger(__name__)


class ConversationManager(AgentInterface):
    """
    Manages conversation flow between scammers and victim personas.
    """
    
    def __init__(
        self,
        llm_client: Any,
        detection_service: ScamDetector,
        intelligence_service: IntelligenceExtractor,
        persona_manager: Optional[PersonaManager] = None
    ):
        self.llm = llm_client
        self.detection_service = detection_service
        self.intelligence_service = intelligence_service
        self.persona_manager = persona_manager or PersonaManager()
        self.variation_engine = VariationEngine()
        self.emotional_intelligence = EmotionalIntelligence()
        self.natural_flow = NaturalConversationFlow()
        self.context_manager = ContextAwareManager()
        self._conversation_contexts: Dict[str, Dict[str, Any]] = {}
    
    @property
    def agent_type(self) -> str:
        return "conversation_manager"
    
    @property
    def capabilities(self) -> List[str]:
        return ["scam_detection", "intelligence_extraction", "persona_management", "conversation_context"]
    
    async def process_message(
        self,
        message: str,
        session: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a scammer message and generate appropriate response.
        """
        session_id = session.get("session_id", "unknown")
        
        try:
            logger.info(f"Processing message for session {session_id}")
            
            # Step 1: Detect scam
            detection_result = await self.detection_service.analyze(
                message=message,
                history=session.get("conversation_history", []),
                metadata=metadata
            )
            
            # Step 2: Extract intelligence
            intelligence_dict = await self.intelligence_service.extract(message)
            
            # Step 4: Generate Guidance
            msg_count = len(session.get("conversation_history", []))
            emotional_guidance = self.emotional_intelligence.get_emotional_guidance(
                session_id, message, msg_count, self.persona_manager._personas[persona_name].config
            )
            stage_guidance = self.natural_flow.get_guidance(session)
            concise_context = self.context_manager.get_context(session)
            
            # Step 5: Build Persona Prompt
            system_prompt = self.persona_manager.get_persona_prompt(persona_name)
            full_system_prompt = f"{system_prompt}\n\nCURRENT CONTEXT: {concise_context}\n\nSTAGE GUIDANCE: {stage_guidance}\n\n{emotional_guidance}"
            
            # Step 6: Generate Base Response
            base_response = await self.llm.generate(
                prompt=f"Scammer message: {message}\n\nVictim's reply:",
                system_prompt=full_system_prompt
            )
            
            # Step 7: Humanize Response
            final_response = self.variation_engine.humanize(
                base_response=base_response,
                persona=self.persona_manager._personas[persona_name].config,
                session_id=session_id,
                message_number=msg_count
            )
            
            return {
                "response": final_response,
                "detection_result": detection_result,
                "intelligence": intelligence_dict,
                "persona_used": persona_name,
                "confidence": detection_result.confidence,
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error(f"Error in conversation session {session_id}: {e}", exc_info=True)
            return {
                "response": "I'm not sure what you mean.",
                "error": str(e)
            }
    
    async def reset_session(self, session_id: str) -> None:
        if session_id in self._conversation_contexts:
            del self._conversation_contexts[session_id]
