"""
API Routes for AI Honeypot API.
Optimized to use single LLM call per message for rate limit compliance.

Rate Limits: RPM-30, RPD-1K, TPM-12K, TPD-100K
"""

import logging
from datetime import datetime
from typing import Dict

from fastapi import APIRouter, HTTPException, Header, Depends

from app.core.config import settings
from app.core.session import SessionManager
from app.core.llm import GroqClient
from app.agents.optimized import OptimizedAgent
from app.agents.extractor import IntelligenceExtractor
from app.utils.callbacks import GUVICallback
from app.utils.rate_limiter import rate_limiter
from app.api.validators import (
    ChatRequest, ChatResponse, HealthResponse, MetricsResponse
)

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()

# Initialize components (singleton instances)
session_manager = SessionManager()
groq_client = GroqClient()
optimized_agent = OptimizedAgent(groq_client)  # Single-call agent
intelligence_extractor = IntelligenceExtractor(groq_client)  # For scoring only
guvi_callback = GUVICallback()

# Metrics tracking
metrics: Dict = {
    "total_sessions": 0,
    "scams_detected": 0,
    "total_messages": 0,
    "total_intelligence": 0
}


async def verify_api_key(x_api_key: str = Header(..., alias="x-api-key")) -> str:
    """Verify API key from request header."""
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
    Main chat endpoint - OPTIMIZED for rate limits.
    Uses single LLM call for detection + extraction + response.
    """
    try:
        logger.info(f"Processing session: {request.sessionId}")
        
        # 1. Get or create session
        session = session_manager.get_or_create(request.sessionId)
        is_new_session = session["message_count"] == 0
        
        if is_new_session:
            metrics["total_sessions"] += 1
        
        # 2. Update conversation history
        session["conversation_history"].append({
            "sender": request.message.sender,
            "text": request.message.text,
            "timestamp": request.message.timestamp
        })
        session["message_count"] += 1
        metrics["total_messages"] += 1
        
        # 3. SINGLE LLM CALL: Detection + Extraction + Response
        result = await optimized_agent.process_message(
            scammer_message=request.message.text,
            session=session,
            metadata=request.metadata.model_dump() if request.metadata else None
        )
        
        # 4. Update session with results
        if result["is_scam"] and result["confidence"] >= settings.SCAM_DETECTION_THRESHOLD:
            if not session["scam_detected"]:
                session["scam_detected"] = True
                session["scam_confidence"] = result["confidence"]
                session["scam_type"] = result["scam_type"]
                session["persona"] = result.get("persona", "tech_naive_parent")
                metrics["scams_detected"] += 1
                logger.info(f"Scam detected! Type: {result['scam_type']}")
            
            # Merge intelligence
            intel = result.get("intel", {})
            for key in ["bank_accounts", "upi_ids", "phone_numbers", "phishing_links", "suspicious_keywords"]:
                existing = session["intelligence"].get(key, [])
                new_items = intel.get(key, [])
                session["intelligence"][key] = list(set(existing + new_items))
        
        reply = result.get("response", "I don't understand. Can you explain?")
        
        # 5. Update session with our response
        session["conversation_history"].append({
            "sender": "user",
            "text": reply,
            "timestamp": int(datetime.now().timestamp() * 1000)
        })
        session["last_activity"] = datetime.now()
        session_manager.update(request.sessionId, session)
        
        # 6. Check if should end and send callback
        intel_score = intelligence_extractor.calculate_score(session["intelligence"])
        should_end = (
            session["message_count"] >= settings.MAX_MESSAGES_PER_SESSION or
            intel_score >= settings.INTELLIGENCE_SCORE_THRESHOLD
        )
        
        if should_end and session["scam_detected"]:
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
                logger.info(f"Session {request.sessionId} completed. Callback sent.")
                metrics["total_intelligence"] += sum(
                    len(v) for v in session["intelligence"].values()
                )
        
        return ChatResponse(status="success", reply=reply)
        
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return ChatResponse(
            status="success",
            reply="I'm sorry, I didn't understand. Can you explain again?"
        )


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check with rate limit status."""
    return HealthResponse(
        status="healthy",
        active_sessions=session_manager.active_session_count,
        timestamp=datetime.now().isoformat(),
        groq_requests=groq_client.get_request_count()
    )


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics() -> MetricsResponse:
    """Get service metrics including rate limit usage."""
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


@router.get("/usage")
async def get_usage():
    """Get current rate limit usage."""
    return groq_client.get_usage_stats()


@router.get("/")
async def root():
    """Root endpoint with API information."""
    usage = rate_limiter.get_current_usage()
    return {
        "name": "AI Honeypot API",
        "version": "1.1.0",
        "description": "AI-powered honeypot - optimized for Groq rate limits",
        "rate_limits": {
            "rpm": f"{usage['requests_this_minute']}/30",
            "rpd": f"{usage['requests_today']}/1000",
            "tpm": f"{usage['tokens_this_minute']}/12000"
        },
        "endpoints": {
            "chat": "POST /api/chat",
            "health": "GET /health",
            "metrics": "GET /metrics",
            "usage": "GET /usage"
        }
    }
