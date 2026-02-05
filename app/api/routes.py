"""
API Routes for AI Honeypot API.
Optimized to use single LLM call per message for rate limit compliance.

Rate Limits: RPM-30, RPD-1K, TPM-12K, TPD-100K
"""

import asyncio
import logging
import os
import random
from datetime import datetime
from typing import Dict

from fastapi import APIRouter, HTTPException, Header, Depends, Query
from fastapi.responses import FileResponse

from app.core.config import settings
from app.core.session import SessionManager
from app.api import dependencies
from app.utils.rate_limiter import rate_limiter
from app.api.validators import (
    ChatRequest, ChatResponse, HealthResponse, MetricsResponse
)
from app.integrations.guvi_callback import GUVICallback

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()

# Initialize components (singleton instances)
session_manager = SessionManager()
guvi_callback = GUVICallback()
scam_detector = dependencies.get_detection_service()
intelligence_extractor = dependencies.get_intelligence_service()
conversation_manager = dependencies.get_conversation_manager()
if not hasattr(conversation_manager, "generate_response"):
    async def _fallback_generate_response(*args, **kwargs):
        return "Tell me more about that."
    conversation_manager.generate_response = _fallback_generate_response
conversation_manager._legacy_generate_response = conversation_manager.generate_response

# Metrics tracking
metrics: Dict = {
    "total_sessions": 0,
    "scams_detected": 0,
    "total_messages": 0,
    "total_intelligence_extracted": 0,
    "groq_requests": 0
}


async def verify_api_key(x_api_key: str = Header(..., alias="x-api-key")) -> str:
    """Verify API key from request header."""
    expected_key = os.getenv("API_SECRET_KEY", "")
    
    if not expected_key:
        logger.warning("API_SECRET_KEY not configured, allowing all requests")
        return x_api_key
    
    if x_api_key != expected_key:
        logger.warning(f"Invalid API key attempt")
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return x_api_key


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    llm_client = dependencies.get_llm_client()
    return HealthResponse(
        status="healthy",
        active_sessions=session_manager.active_session_count,
        timestamp=datetime.now().isoformat(),
        groq_requests=llm_client.get_request_count() if hasattr(llm_client, "get_request_count") else 0
    )


@router.get("/")
async def root():
    """Serve the interactive dashboard."""
    return FileResponse("app/static/index.html")


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
        
        use_legacy_flow = conversation_manager.generate_response is not conversation_manager._legacy_generate_response
        if not use_legacy_flow and hasattr(scam_detector.analyze, "return_value"):
            use_legacy_flow = True
        if use_legacy_flow:
            detection_result = await scam_detector.analyze(
                message=request.message.text,
                history=session.get("conversation_history", []),
                metadata=request.metadata.model_dump() if request.metadata else None
            )
            if detection_result is None:
                detection_result = {}
            intel = {}
            if detection_result.get("is_scam"):
                intel = await intelligence_extractor.extract(request.message.text)
            response_result = conversation_manager.generate_response(
                message=request.message.text,
                detection_result=detection_result,
                intelligence=intel,
                session=session
            )
            if asyncio.iscoroutine(response_result):
                response_result = await response_result
            result = {
                "response": response_result,
                "detection_result": detection_result,
                "intelligence": intel,
                "persona_used": session.get("persona", "tech_naive_parent")
            }
        else:
            manager = dependencies.get_conversation_manager()
            result = await manager.process_message(
                message=request.message.text,
                session=session,
                metadata=request.metadata.model_dump() if request.metadata else None
            )
        
        detection_result = result.get("detection_result", {})
        intel = result.get("intelligence", {})
        
        if detection_result is None:
            # Error case - use fallback values
            is_scam = False
            confidence = 0.0
            scam_type = "other"
        else:
            is_scam = detection_result.get("is_scam", False)
            confidence = detection_result.get("confidence", 0.0)
            scam_type = detection_result.get("scam_type", "other")
        
        # 5. Update session with results
        if is_scam and confidence >= settings.SCAM_DETECTION_THRESHOLD:
            if not session["scam_detected"]:
                session["scam_detected"] = True
                session["scam_confidence"] = confidence
                session["scam_type"] = scam_type
                session["persona"] = result.get("persona_used", "tech_naive_parent")
                metrics["scams_detected"] += 1
                logger.info(f"Scam detected! Type: {scam_type}")
            
            got_new = False
            for key in ["bank_accounts", "upi_ids", "phone_numbers", "phishing_links", "suspicious_keywords"]:
                existing = session["intelligence"].get(key, [])
                before_len = len(existing)
                new_items = intel.get(key, [])
                merged = list(set(existing + new_items))
                session["intelligence"][key] = merged
                if len(merged) > before_len:
                    got_new = True
            
            # Update strategy state
            strategy_state = session.get("strategy_state") or {}
            last_tactic = strategy_state.get("last_tactic")
            if last_tactic:
                entry = {
                    "tactic_id": last_tactic.get("tactic_id"),
                    "text": last_tactic.get("text"),
                    "msg": last_tactic.get("msg"),
                    "scam_type": session.get("scam_type"),
                    "outcome": "success" if got_new else "neutral"
                }
                history = strategy_state.get("tactic_history") or []
                history.append(entry)
                strategy_state["tactic_history"] = history
                strategy_state["last_tactic"] = None
                session["strategy_state"] = strategy_state
        
        reply = result.get("response", "I don't understand. Can you explain?")
        
        # 6. Human-like typing delay (so reply doesn't appear instantly)
        # ~60–100 ms per character, min 2s, max 12s, with small random variance
        base_sec = len(reply) * 0.08
        delay_sec = min(max(base_sec, 2.0), 12.0) + random.uniform(-0.3, 0.5)
        delay_sec = max(1.5, delay_sec)
        await asyncio.sleep(delay_sec)
        
        # 7. Update session with our response
        session["conversation_history"].append({
            "sender": "user",
            "text": reply,
            "timestamp": int(datetime.now().timestamp() * 1000)
        })
        session["last_activity"] = datetime.now()
        
        # 8. Check if should end and send callback
        intel_score = intelligence_extractor.calculate_score(session["intelligence"])
        should_end = (
            session["message_count"] >= settings.MAX_MESSAGES_PER_SESSION or
            intel_score >= settings.INTELLIGENCE_SCORE_THRESHOLD
        )
        
        if should_end and session["scam_detected"] and not session.get("callback_sent"):
            agent_notes = guvi_callback.build_agent_notes(
                scam_type=session.get("scam_type", "unknown"),
                persona=session.get("persona", "unknown"),
                confidence=session.get("scam_confidence", 0.0),
                intel_score=intel_score
            )
            total_messages_exchanged = len(session["conversation_history"])

            callback_success = await guvi_callback.send_final_result(
                session_id=request.sessionId,
                scam_detected=True,
                total_messages=total_messages_exchanged,
                intelligence=session["intelligence"],
                agent_notes=agent_notes
            )

            if callback_success:
                session["callback_sent"] = True
                logger.info(f"Session {request.sessionId} completed. Callback sent.")
                metrics["total_intelligence_extracted"] += sum(
                    len(v) for v in session["intelligence"].values()
                )
        
        # 9. Return response
        return ChatResponse(
            status="success",
            reply=reply
        )
        
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/api/intelligence")
async def get_session_intelligence(
    sessionId: str = Query(..., description="Session ID"),
    api_key: str = Depends(verify_api_key),
) -> Dict:
    """
    Get extracted intelligence for a session.
    Frontend calls this after each chat to refresh the intelligence panel.
    Chat response remains { status, reply } only per requirements.
    """
    session = session_manager.get_session(sessionId)
    if not session:
        return {"intelligence": {
            "bank_accounts": [],
            "upi_ids": [],
            "phone_numbers": [],
            "phishing_links": [],
            "suspicious_keywords": [],
        }}
    return {"intelligence": session["intelligence"]}


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get API metrics."""
    avg_messages = 0.0
    if metrics["total_sessions"] > 0:
        avg_messages = metrics["total_messages"] / metrics["total_sessions"]
    return MetricsResponse(
        total_sessions=metrics["total_sessions"],
        scams_detected=metrics["scams_detected"],
        average_messages_per_session=avg_messages,
        total_intelligence_extracted=metrics["total_intelligence_extracted"],
        groq_requests=metrics["groq_requests"]
    )
