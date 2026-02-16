"""
GUVI Callback Handler for AI Honeypot API.
Sends final intelligence reports to GUVI's evaluation endpoint.
"""

import logging
from typing import Dict
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class GUVICallback:
    """Handles sending final results to GUVI's callback endpoint."""
    
    def __init__(self, callback_url: str = None):
        self.callback_url = callback_url or settings.GUVI_CALLBACK_URL
    
    async def send_final_result(
        self,
        session_id: str,
        scam_detected: bool,
        total_messages: int,
        intelligence: Dict,
        agent_notes: str,
        engagement_metrics: Dict = None
    ) -> bool:
        """
        Send final intelligence report to GUVI endpoint.
        
        Args:
            session_id: Unique session identifier
            scam_detected: Whether scam was detected
            total_messages: Total message exchanges
            intelligence: Extracted intelligence dictionary
            agent_notes: Additional notes about the session
        
        Returns:
            True if callback successful, False otherwise
        """
        # Build payload with camelCase keys as expected by evaluator
        payload = {
            "sessionId": session_id,
            "status": "completed",
            "scamDetected": scam_detected,
            "totalMessagesExchanged": total_messages,
            "extractedIntelligence": {
                "bankAccounts": intelligence.get("bank_accounts", []),
                "upiIds": intelligence.get("upi_ids", []),
                "phishingLinks": intelligence.get("phishing_links", []),
                "phoneNumbers": intelligence.get("phone_numbers", []),
                "emailAddresses": intelligence.get("email_addresses", []),
                "suspiciousKeywords": intelligence.get("suspicious_keywords", [])
            },
            "engagementMetrics": engagement_metrics or {
                "totalMessagesExchanged": total_messages,
                "engagementDurationSeconds": 0
            },
            "agentNotes": agent_notes
        }
        
        logger.info(f"Sending callback for session {session_id}")
        logger.debug(f"Callback payload: {payload}")
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    self.callback_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    logger.info(f"✓ Callback successful for session {session_id}")
                    return True
                else:
                    logger.error(
                        f"✗ Callback failed for session {session_id}: "
                        f"Status {response.status_code} - {response.text}"
                    )
                    return False
                    
        except httpx.TimeoutException:
            logger.error(f"✗ Callback timeout for session {session_id}")
            return False
        except Exception as e:
            logger.error(f"✗ Callback error for session {session_id}: {str(e)}")
            return False
    
    def build_agent_notes(
        self,
        scam_type: str,
        persona: str,
        confidence: float,
        intel_score: float
    ) -> str:
        """
        Build agent notes string for callback.
        
        Args:
            scam_type: Detected scam type
            persona: Used persona name
            confidence: Detection confidence
            intel_score: Intelligence quality score
        
        Returns:
            Formatted agent notes string
        """
        return (
            f"Scam type: {scam_type}. "
            f"Persona: {persona}. "
            f"Detection confidence: {confidence:.2f}. "
            f"Intelligence score: {intel_score:.2f}"
        )
