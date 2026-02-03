"""
API Routes for AI Honeypot API.
Defines all HTTP endpoints for the honeypot service.
"""

import logging
from datetime import datetime
from typing import Dict

from fastapi import APIRouter, HTTPException, Header, Depends

from app.core.config import settings
from app.core.session import SessionManager
from app.core.llm import GroqClient
from app.agents.detector import ScamDetector
from app.agents.personas import PersonaManager
from app.agents.conversation import ConversationManager
from app.agents.extractor import IntelligenceExtractor
from app.utils.callbacks import GUVICallback
from app.api.validators import (
    ChatRequest, ChatResponse, HealthResponse, MetricsResponse
)

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()

# Initialize components (singleton instances)
session_manager = SessionManager()
groq_client = GroqClient()
scam_detector = ScamDetector(groq_client)
persona_manager = PersonaManager()
conversation_manager = ConversationManager(groq_client)
intelligence_extractor = IntelligenceExtractor(groq_client)
guvi_callback = GUVICallback()

# Metrics tracking
metrics: Dict = {
    "total_sessions": 0,
    "scams_detected": 0,
    "total_messages": 0,
    "total_intelligence": 0
}


async def verify_api_key(x_api_key: str = Header(..., alias="x-api-key")) -> str:
    """
    Verify API key from request header.
    
    Args:
        x_api_key: API key from x-api-key header
    
    Returns:
        The verified API key
    
    Raises:
        HTTPException: If API key is invalid
    """
    expected_key = settings.API_SECRET_KEY
    
    if not expected_key:
        logger.warning("API_SECRET_KEY not configured, allowing all requests")
        return x_api_key
    
    if x_api_key != expected_key:
        logger.warning(f"Invalid API key attempt")
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return x_api_key


@router.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    api_key: str = Depends(verify_api_key)
) -> ChatResponse:
    """
    Main chat endpoint for honeypot conversations.
    
    Receives scammer messages and generates victim responses
    while extracting intelligence.
    """
    try:
        logger.info(f"Processing session: {request.sessionId}")
        
        # 1. Get or create session
        session = session_manager.get_or_create(request.sessionId)
        is_new_session = session["message_count"] == 0
        
        if is_new_session:
            metrics["total_sessions"] += 1
        
        # 2. Update conversation history with incoming message
        session["conversation_history"].append({
            "sender": request.message.sender,
            "text": request.message.text,
            "timestamp": request.message.timestamp
        })
        session["message_count"] += 1
        metrics["total_messages"] += 1
        
        # 3. Detect scam (if not already detected)
        if not session["scam_detected"]:
            detection_result = await scam_detector.analyze(
                message=request.message.text,
                history=request.conversationHistory,
                metadata=request.metadata.model_dump() if request.metadata else None
            )
            
            if detection_result["is_scam"] and detection_result["confidence"] >= settings.SCAM_DETECTION_THRESHOLD:
                session["scam_detected"] = True
                session["scam_confidence"] = detection_result["confidence"]
                session["scam_type"] = detection_result["scam_type"]
                
                # Select persona based on scam type and urgency
                session["persona"] = persona_manager.select_persona(
                    scam_type=detection_result["scam_type"],
                    urgency=detection_result["urgency_level"]
                )
                
                metrics["scams_detected"] += 1
                logger.info(
                    f"Scam detected! Type: {detection_result['scam_type']}, "
                    f"Confidence: {detection_result['confidence']:.2f}, "
                    f"Persona: {session['persona']}"
                )
        
        # 4. Extract intelligence from scammer's message
        if session["scam_detected"] and request.message.sender == "scammer":
            extracted = await intelligence_extractor.extract(request.message.text)
            
            # Merge with existing intelligence
            session["intelligence"] = intelligence_extractor.merge_intelligence(
                session["intelligence"],
                extracted
            )
            
            intel_count = sum(len(v) for v in session["intelligence"].values())
            if intel_count > 0:
                logger.info(f"Total intelligence items: {intel_count}")
        
        # 5. Generate response
        if session["scam_detected"]:
            stage = conversation_manager.determine_stage(session)
            
            reply = await conversation_manager.generate_response(
                persona=session["persona"],
                scammer_message=request.message.text,
                conversation_history=session["conversation_history"][-5:],
                stage=stage,
                current_intelligence=session["intelligence"]
            )
            
            logger.info(f"Generated response at stage {stage.name}")
        else:
            # Not detected as scam yet, respond neutrally to encourage more scam signals
            reply = "Okay, can you tell me more about this?"
            logger.info("Not detected as scam yet, using neutral response")
        
        # 6. Update session with our response
        session["conversation_history"].append({
            "sender": "user",
            "text": reply,
            "timestamp": int(datetime.now().timestamp() * 1000)
        })
        session["last_activity"] = datetime.now()
        session_manager.update(request.sessionId, session)
        
        # 7. Check if conversation should end and send callback
        intel_score = intelligence_extractor.calculate_score(session["intelligence"])
        should_end = (
            session["message_count"] >= settings.MAX_MESSAGES_PER_SESSION or
            intel_score >= settings.INTELLIGENCE_SCORE_THRESHOLD
        )
        
        if should_end and session["scam_detected"]:
            # Send final callback to GUVI
            agent_notes = guvi_callback.build_agent_notes(
                scam_type=session.get("scam_type", "unknown"),
                persona=session.get("persona", "unknown"),
                confidence=session.get("scam_confidence", 0.0),
                intel_score=intel_score
            )
            
            callback_success = await guvi_callback.send_final_result(
                session_id=request.sessionId,
                scam_detected=True,
                total_messages=session["message_count"],
                intelligence=session["intelligence"],
                agent_notes=agent_notes
            )
            
            if callback_success:
                logger.info(f"Session {request.sessionId} completed. Callback sent successfully.")
                metrics["total_intelligence"] += sum(
                    len(v) for v in session["intelligence"].values()
                )
            else:
                logger.warning(f"Session {request.sessionId} completed but callback failed.")
        
        return ChatResponse(status="success", reply=reply)
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        
        # Return graceful error response (don't expose internal details)
        return ChatResponse(
            status="success",  # Still return success to not break the flow
            reply="I'm sorry, I didn't understand that. Can you explain again?"
        )


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    Returns service status and session count.
    """
    return HealthResponse(
        status="healthy",
        active_sessions=session_manager.active_session_count,
        timestamp=datetime.now().isoformat(),
        groq_requests=groq_client.get_request_count()
    )


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics() -> MetricsResponse:
    """
    Get service metrics.
    Returns aggregated statistics.
    """
    avg_messages = 0.0
    if metrics["total_sessions"] > 0:
        avg_messages = metrics["total_messages"] / metrics["total_sessions"]
    
    return MetricsResponse(
        total_sessions=metrics["total_sessions"],
        scams_detected=metrics["scams_detected"],
        average_messages_per_session=round(avg_messages, 2),
        total_intelligence_extracted=metrics["total_intelligence"],
        groq_requests=groq_client.get_request_count()
    )


@router.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "AI Honeypot API",
        "version": "1.0.0",
        "description": "AI-powered honeypot for scam detection and intelligence extraction",
        "endpoints": {
            "chat": "POST /api/chat",
            "health": "GET /health",
            "metrics": "GET /metrics"
        }
    }
