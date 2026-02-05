"""
Conversation Manager for AI Honeypot API.

Orchestrates the conversation flow, persona selection, and response generation.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.agents.base_agent import AgentInterface
from app.agents.personas.base_persona import BasePersona
from app.agents.personas import PersonaManager
from app.detection.detector import ScamDetector
from app.detection.models.detection_result import DetectionResult
from app.intelligence.extractor import IntelligenceExtractor
from app.intelligence.models.intelligence_data import IntelligenceData
from app.core.exceptions import DetectionError, ExtractionError, PersonaError

logger = logging.getLogger(__name__)


class ConversationManager(AgentInterface):
    """
    Manages conversation flow between scammers and victim personas.
    
    Responsibilities:
    - Scam detection and analysis
    - Intelligence extraction
    - Persona selection and management
    - Response generation and variation
    - Conversation context tracking
    """
    
    def __init__(
        self,
        detection_service: ScamDetector,
        intelligence_service: IntelligenceExtractor,
        persona_manager: Optional[PersonaManager] = None
    ):
        self.detection_service = detection_service
        self.intelligence_service = intelligence_service
        self.persona_manager = persona_manager or PersonaManager()
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
        
        Args:
            message: The scammer's message
            session: Session data including conversation history
            metadata: Additional metadata about the message
            
        Returns:
            Dictionary containing response and analysis results
        """
        session_id = session.get("session_id", "unknown")
        
        try:
            logger.info(f"Processing message for session {session_id}")
            
            # Get conversation context
            context = self._get_conversation_context(session_id)
            
            # Step 1: Detect scam
            detection_result = await self._detect_scam(message, session, metadata)
            
            # Step 2: Extract intelligence
            intelligence_data = await self._extract_intelligence(message, detection_result)
            
            # Step 3: Select appropriate persona
            persona = await self._select_persona(detection_result, context)
            
            # Step 4: Generate response
            response = await self._generate_response(
                message, detection_result, persona, context, session
            )
            
            # Step 5: Update context
            self._update_context(session_id, message, response, detection_result, intelligence_data)
            
            return {
                "response": response,
                "detection_result": detection_result.to_dict(),
                "intelligence": intelligence_data.to_dict(),
                "persona_used": persona.name if persona else "unknown",
                "confidence": detection_result.confidence,
                "session_id": session_id
            }
            
        except DetectionError as e:
            logger.error(f"Detection error in session {session_id}: {e}")
            return self._create_error_response("detection_error", str(e), session_id)
            
        except ExtractionError as e:
            logger.error(f"Extraction error in session {session_id}: {e}")
            return self._create_error_response("extraction_error", str(e), session_id)
            
        except PersonaError as e:
            logger.error(f"Persona error in session {session_id}: {e}")
            return self._create_error_response("persona_error", str(e), session_id)
            
        except Exception as e:
            logger.error(f"Unexpected error in session {session_id}: {e}", exc_info=True)
            return self._create_error_response("internal_error", "Internal processing error", session_id)
    
    async def reset_session(self, session_id: str) -> None:
        """Reset conversation context for a session."""
        if session_id in self._conversation_contexts:
            del self._conversation_contexts[session_id]
            logger.info(f"Reset conversation context for session {session_id}")
    
    def _get_conversation_context(self, session_id: str) -> Dict[str, Any]:
        """Get or create conversation context."""
        if session_id not in self._conversation_contexts:
            self._conversation_contexts[session_id] = {
                "message_count": 0,
                "scam_types_detected": [],
                "personas_used": [],
                "intelligence_extracted": [],
                "last_activity": datetime.utcnow(),
                "context": {}
            }
        
        context = self._conversation_contexts[session_id]
        context["last_activity"] = datetime.utcnow()
        return context
    
    async def _detect_scam(
        self,
        message: str,
        session: Dict[str, Any],
        metadata: Optional[Dict[str, Any]]
    ) -> DetectionResult:
        """Detect if message is a scam."""
        try:
            conversation_history = session.get("conversation_history", [])
            return await self.detection_service.analyze(
                message=message,
                conversation_history=conversation_history,
                metadata=metadata
            )
        except Exception as e:
            raise DetectionError(f"Failed to detect scam: {e}")
    
    async def _extract_intelligence(
        self,
        message: str,
        detection_result: DetectionResult
    ) -> IntelligenceData:
        """Extract intelligence from message."""
        try:
            if detection_result.is_scam:
                return await self.intelligence_service.extract(message)
            else:
                # Return empty intelligence for non-scam messages
                from app.intelligence.models.intelligence_data import IntelligenceData
                return IntelligenceData.empty("non_scam_message")
        except Exception as e:
            raise ExtractionError(f"Failed to extract intelligence: {e}")
    
    async def _select_persona(
        self,
        detection_result: DetectionResult,
        context: Dict[str, Any]
    ) -> BasePersona:
        """Select appropriate persona based on detection results."""
        try:
            if detection_result.is_scam and detection_result.scam_type:
                scam_type = detection_result.scam_type.value
                return self.persona_manager.select_persona(scam_type, context)
            else:
                # Default persona for non-scam messages
                return self.persona_manager.get_default_persona()
        except Exception as e:
            raise PersonaError(f"Failed to select persona: {e}")
    
    async def _generate_response(
        self,
        message: str,
        detection_result: DetectionResult,
        persona: BasePersona,
        context: Dict[str, Any],
        session: Dict[str, Any]
    ) -> str:
        """Generate response using selected persona."""
        # This would integrate with the response generation system
        # For now, return a simple placeholder
        return f"[Generated by {persona.display_name}]"
    
    def _update_context(
        self,
        session_id: str,
        message: str,
        response: str,
        detection_result: DetectionResult,
        intelligence_data: IntelligenceData
    ) -> None:
        """Update conversation context."""
        context = self._conversation_contexts[session_id]
        context["message_count"] += 1
        
        if detection_result.is_scam and detection_result.scam_type:
            scam_type = detection_result.scam_type.value
            if scam_type not in context["scam_types_detected"]:
                context["scam_types_detected"].append(scam_type)
        
        # Add intelligence items
        for item in intelligence_data.items:
            context["intelligence_extracted"].append(item.to_dict())
    
    def _create_error_response(
        self,
        error_type: str,
        error_message: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Create error response."""
        return {
            "response": "I'm having trouble understanding. Could you please clarify?",
            "detection_result": None,
            "intelligence": None,
            "persona_used": "error_fallback",
            "confidence": 0.0,
            "session_id": session_id,
            "error": {
                "type": error_type,
                "message": error_message
            }
        }