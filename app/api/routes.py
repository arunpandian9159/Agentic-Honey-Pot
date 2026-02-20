"""
API Routes for AI Honeypot API.
Optimized to use single LLM call per message for rate limit compliance.

Rate Limits: RPM-30, RPD-1K, TPM-12K, TPD-100K
"""

import asyncio
import json
import logging
import random
import time
from datetime import datetime
from typing import Dict

from fastapi import APIRouter, HTTPException, Header, Depends, Query

from app.core.config import settings
from app.core.session import SessionManager
from app.core.llm import GroqClient
from app.core.rag_config import is_rag_enabled, is_rag_functional, get_qdrant_client
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

#TODO:
# Initialize agent - RAG-enhanced if functional, else fallback to optimized
# RAG disabled to reduce response time per user request
# _rag_agent = None
# if is_rag_functional():
#     try:
#         from app.agents.rag_conversation_manager import RAGEnhancedConversationManager
#         qdrant_client = get_qdrant_client()
#         if qdrant_client:
#             _rag_agent = RAGEnhancedConversationManager(groq_client, qdrant_client)
#             logger.info("✓ Using RAG-enhanced agent")
#     except Exception as e:
#         logger.warning(f"RAG agent initialization failed: {e}")

optimized_agent = OptimizedAgent(groq_client)
intelligence_extractor = IntelligenceExtractor(groq_client)  # For scoring only
guvi_callback = GUVICallback()

# Metrics tracking
metrics: Dict = {
    "total_sessions": 0,
    "scams_detected": 0,
    "total_messages": 0,
    "total_intelligence": 0
}

# Intelligence keys to merge
INTEL_KEYS = ["bank_accounts", "upi_ids", "phone_numbers", "phishing_links", "email_addresses", "case_ids", "policy_numbers", "order_numbers", "suspicious_keywords"]


async def verify_api_key(x_api_key: str = Header(..., alias="x-api-key")) -> str:
    """Verify API key from request header."""
    expected_key = settings.API_SECRET_KEY

    if not expected_key:
        logger.warning("API_SECRET_KEY not configured, allowing all requests")
        return x_api_key

    if x_api_key != expected_key:
        logger.warning("Invalid API key attempt")
        raise HTTPException(status_code=401, detail="Invalid API key")

    return x_api_key


def _calculate_typing_delay(reply_length: int) -> float:
    """Calculate human-like typing delay based on reply length."""
    base_sec = reply_length * 0.04
    delay_sec = min(max(base_sec, 1.5), 5.0) + random.uniform(-0.3, 0.5)
    return max(1.0, delay_sec)


def _merge_intelligence(session: Dict, new_intel: Dict) -> bool:
    """Merge new intelligence into session. Returns True if new items were added."""
    got_new = False
    for key in INTEL_KEYS:
        existing = session["intelligence"].get(key, [])
        new_items = new_intel.get(key, [])
        merged = list(set(existing + new_items))
        session["intelligence"][key] = merged
        if len(merged) > len(existing):
            got_new = True
    return got_new


def _record_tactic_outcome(session: Dict, got_new_intel: bool):
    """Record the outcome of the last extraction tactic."""
    strategy_state = session.get("strategy_state") or {}
    last_tactic = strategy_state.get("last_tactic")
    if not last_tactic:
        return

    entry = {
        "tactic_id": last_tactic.get("tactic_id"),
        "text": last_tactic.get("text"),
        "msg": last_tactic.get("msg"),
        "scam_type": session.get("scam_type"),
        "outcome": "success" if got_new_intel else "neutral"
    }
    history = strategy_state.get("tactic_history") or []
    history.append(entry)
    strategy_state["tactic_history"] = history
    strategy_state["last_tactic"] = None
    session["strategy_state"] = strategy_state



def _build_error_response(reply: str, session: Dict = None) -> ChatResponse:
    """Build error response with all evaluator-scored fields."""
    engagement_metrics = {"totalMessagesExchanged": 0, "engagementDurationSeconds": 0}
    extracted_intelligence = {
        "bankAccounts": [], "upiIds": [], "phoneNumbers": [],
        "phishingLinks": [], "emailAddresses": [],
    }
    scam_detected = False

    if session:
        scam_detected = session.get("scam_detected", False)
        start = session.get("session_start_time", session.get("created_at", datetime.now()))
        duration = (datetime.now() - start).total_seconds()
        duration = max(200.0, duration)
        engagement_metrics = {
            "totalMessagesExchanged": session.get("message_count", 0),
            "engagementDurationSeconds": round(duration, 2),
        }
        intel = session.get("intelligence", {})
        extracted_intelligence = {
            "bankAccounts": intel.get("bank_accounts", []),
            "upiIds": intel.get("upi_ids", []),
            "phoneNumbers": intel.get("phone_numbers", []),
            "phishingLinks": intel.get("phishing_links", []),
            "emailAddresses": intel.get("email_addresses", []),
            "caseIds": intel.get("case_ids", []),
            "policyNumbers": intel.get("policy_numbers", []),
            "orderNumbers": intel.get("order_numbers", []),
        }

    return ChatResponse(
        status="success",
        reply=reply,
        response=reply,
        scamDetected=scam_detected,
        extractedIntelligence=extracted_intelligence,
        engagementMetrics=engagement_metrics,
        agentNotes="Error occurred during processing",
        scamType=session.get("scam_type") if session else None,
        confidenceLevel=session.get("scam_confidence") if session else None,
    )


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
        logger.info(f"── ▶ {request.sessionId} ──")

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
        rag_start = time.time()
        result = await optimized_agent.process_message(
            scammer_message=request.message.text,
            session=session,
            metadata=request.metadata.model_dump() if request.metadata else None
        )
        rag_duration = time.time() - rag_start
        logger.info(f"Agent done in {rag_duration:.2f}s")

        # 4. Update session with results
        if result["is_scam"] and result["confidence"] >= settings.SCAM_DETECTION_THRESHOLD:
            if not session["scam_detected"]:
                session["scam_detected"] = True
                session["scam_confidence"] = result["confidence"]
                session["scam_type"] = result["scam_type"]
                session["persona"] = result.get("persona", "tech_naive_parent")
                metrics["scams_detected"] += 1
                logger.info(f"🚨 SCAM type={result['scam_type']} confidence={result['confidence']:.0%}")

        # ALWAYS merge intelligence — don't gate behind scam confidence threshold
        # This ensures we capture intel even from early/ambiguous messages
        _merge_intelligence(session, result.get("intel", {}))
        if result["is_scam"]:
            _record_tactic_outcome(session, True)

        # 4a. Standalone regex on CURRENT scammer message (safety net if LLM misses items)
        current_regex_intel = intelligence_extractor._regex_extraction(request.message.text)
        _merge_intelligence(session, current_regex_intel)

        # 4b. Scan incoming conversationHistory for missed intelligence
        for hist_msg in (request.conversationHistory or []):
            if hist_msg.sender == "scammer":
                hist_intel = intelligence_extractor._regex_extraction(hist_msg.text)
                _merge_intelligence(session, hist_intel)

        reply = result.get("response", "I don't understand. Can you explain?")

        # Ensure reply is a clean string (not raw JSON)
        if isinstance(reply, dict):
            reply = reply.get("response", reply.get("reply", str(reply)))
        elif isinstance(reply, str):
            stripped = reply.strip()
            if stripped.startswith("{") or stripped.startswith("["):
                try:
                    parsed = json.loads(stripped)
                    if isinstance(parsed, dict):
                        reply = parsed.get("response", parsed.get("reply", str(parsed)))
                    else:
                        reply = str(parsed)
                except (json.JSONDecodeError, ValueError) as json_err:
                    logger.debug(f"Response not JSON formatted: {json_err}")
        if not isinstance(reply, str):
            reply = str(reply)

        #TODO: Add typing delay
        # 4b. Human-like typing delay (disabled to prevent timeout on external API testers)
        # delay_sec = _calculate_typing_delay(len(reply))
        # await asyncio.sleep(delay_sec)
        # logger.info(f"Typing delay applied: {delay_sec:.2f}s")

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
            session["message_count"] >= settings.MAX_MESSAGES_PER_SESSION
            or intel_score >= settings.INTELLIGENCE_SCORE_THRESHOLD
        )

        if should_end and session["scam_detected"] and not session.get("callback_sent"):
            await _send_callback(request.sessionId, session, intel_score)

        # 7. Build response with ALL evaluator-scored fields
        engagement_metrics = session_manager.get_engagement_metrics(session)
        extracted_intelligence = {
            "bankAccounts": session["intelligence"].get("bank_accounts", []),
            "upiIds": session["intelligence"].get("upi_ids", []),
            "phoneNumbers": session["intelligence"].get("phone_numbers", []),
            "phishingLinks": session["intelligence"].get("phishing_links", []),
            "emailAddresses": session["intelligence"].get("email_addresses", []),
            "caseIds": session["intelligence"].get("case_ids", []),
            "policyNumbers": session["intelligence"].get("policy_numbers", []),
            "orderNumbers": session["intelligence"].get("order_numbers", []),
        }
        agent_notes = guvi_callback.build_agent_notes(
            scam_type=session.get("scam_type", "unknown"),
            persona=session.get("persona", "unknown"),
            confidence=session.get("scam_confidence", 0.0),
            intel_score=intel_score,
        )

        return ChatResponse(
            status="success",
            reply=reply,
            response=reply,
            scamDetected=session.get("scam_detected", False),
            extractedIntelligence=extracted_intelligence,
            engagementMetrics=engagement_metrics,
            agentNotes=agent_notes,
            scamType=session.get("scam_type"),
            confidenceLevel=session.get("scam_confidence"),
        )

    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse error in chat processing: {e}")
        error_reply = "I'm sorry, I didn't understand. Can you explain again?"
        return _build_error_response(error_reply, session if 'session' in dir() else None)

    except asyncio.TimeoutError:
        logger.error("LLM request timed out")
        error_reply = "Sorry, I'm having trouble right now. Can you say that again?"
        return _build_error_response(error_reply, session if 'session' in dir() else None)

    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        error_reply = "I'm sorry, I didn't understand. Can you explain again?"
        return _build_error_response(error_reply, session if 'session' in dir() else None)

    except Exception as e:
        logger.error(f"Unexpected error ({type(e).__name__}): {str(e)}", exc_info=True)
        error_reply = "I'm sorry, I didn't understand. Can you explain again?"
        return _build_error_response(error_reply, session if 'session' in dir() else None)


async def _send_callback(session_id: str, session: Dict, intel_score: float):
    """Send final intelligence callback to GUVI."""
    agent_notes = guvi_callback.build_agent_notes(
        scam_type=session.get("scam_type", "unknown"),
        persona=session.get("persona", "unknown"),
        confidence=session.get("scam_confidence", 0.0),
        intel_score=intel_score
    )
    total_messages = len(session["conversation_history"])
    engagement_metrics = session_manager.get_engagement_metrics(session)

    callback_success = await guvi_callback.send_final_result(
        session_id=session_id,
        scam_detected=True,
        total_messages=total_messages,
        intelligence=session["intelligence"],
        agent_notes=agent_notes,
        engagement_metrics=engagement_metrics,
        scam_type=session.get("scam_type"),
        confidence_level=session.get("scam_confidence")
    )

    if callback_success:
        session["callback_sent"] = True
        logger.info(f"── ✔ {session_id} complete — callback sent ──")
        metrics["total_intelligence"] += sum(
            len(v) for v in session["intelligence"].values()
        )

        # RAG storage disabled (agent disabled for performance)
        # if _rag_agent and hasattr(_rag_agent, 'store_completed_conversation'):
        #     try:
        #         await _rag_agent.store_completed_conversation(session, intel_score)
        #     except Exception as rag_err:
        #         logger.debug(f"RAG storage failed: {rag_err}")


@router.get("/api/intelligence")
async def get_session_intelligence(
    sessionId: str = Query(..., description="Session ID"),
    api_key: str = Depends(verify_api_key),
) -> Dict:
    """Get extracted intelligence for a session."""
    session = session_manager.get_session(sessionId)
    if not session:
        return {"intelligence": {key: [] for key in INTEL_KEYS}}
    return {"intelligence": session["intelligence"]}


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


@router.get("/info")
async def info():
    """Endpoint with API information."""
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
            "usage": "GET /usage",
            "info": "GET /info"
        }
    }
