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
        agent_notes: str
    ) -> bool:
        """
        Send final intelligence report to GUVI endpoint.
        """
        # Build payload with camelCase keys as expected by GUVI
        payload = {
            "sessionId": session_id,
            "scamDetected": scam_detected,
            "totalMessagesExchanged": total_messages,
            "extractedIntelligence": {
                "bankAccounts": intelligence.get("bank_accounts", []),
                "upiIds": intelligence.get("upi_ids", []),
                "phishingLinks": intelligence.get("phishing_links", []),
                "phoneNumbers": intelligence.get("phone_numbers", []),
                "suspiciousKeywords": intelligence.get("suspicious_keywords", [])
            },
            "agentNotes": agent_notes
        }
        
        logger.info(f"Sending callback for session {session_id}")
        
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
        """
        return (
            f"Scam type: {scam_type}. "
            f"Persona: {persona}. "
            f"Detection confidence: {confidence:.2f}. "
            f"Intelligence score: {intel_score:.2f}"
        )
