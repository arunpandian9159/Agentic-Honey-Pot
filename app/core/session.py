"""
Session management for AI Honeypot API.
In-memory session storage with automatic cleanup.
"""

from typing import Dict, Optional
from datetime import datetime, timedelta
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages conversation sessions in memory."""
    
    def __init__(self):
        self.sessions: Dict[str, Dict] = {}
        self.session_timeout = timedelta(minutes=settings.SESSION_TIMEOUT_MINUTES)
    
    def _create_empty_session(self, session_id: str) -> Dict:
        """Create a new empty session structure."""
        return {
            "session_id": session_id,
            "conversation_history": [],
            "scam_detected": False,
            "scam_confidence": 0.0,
            "scam_type": None,
            "persona": None,
            "intelligence": {
                "bank_accounts": [],
                "upi_ids": [],
                "phishing_links": [],
                "phone_numbers": [],
                "email_addresses": [],
                "suspicious_keywords": []
            },
            "strategy_state": {
                "tactic_history": [],
                "last_tactic": None
            },
            "message_count": 0,
            "callback_sent": False,
            "session_start_time": datetime.now(),
            "created_at": datetime.now(),
            "last_activity": datetime.now()
        }
    
    def get_or_create(self, session_id: str) -> Dict:
        """Get existing session or create a new one."""
        # Clean up expired sessions first
        self._cleanup_expired()
        
        if session_id in self.sessions:
            logger.info(f"Retrieved existing session: {session_id}")
            return self.sessions[session_id]
        
        # Create new session
        session = self._create_empty_session(session_id)
        self.sessions[session_id] = session
        logger.info(f"Created new session: {session_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get a session by ID, returns None if not found."""
        return self.sessions.get(session_id)
    
    def update(self, session_id: str, session_data: Dict) -> None:
        """Update session data."""
        session_data["last_activity"] = datetime.now()
        self.sessions[session_id] = session_data
        logger.debug(f"Updated session: {session_id}")
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session by ID."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Deleted session: {session_id}")
            return True
        return False
    
    def _cleanup_expired(self) -> None:
        """Remove sessions older than timeout."""
        now = datetime.now()
        expired = [
            sid for sid, session in self.sessions.items()
            if now - session["last_activity"] > self.session_timeout
        ]
        
        for sid in expired:
            del self.sessions[sid]
            logger.info(f"Cleaned up expired session: {sid}")
    
    def get_engagement_metrics(self, session: Dict) -> Dict:
        """Calculate engagement metrics for scoring."""
        start = session.get("session_start_time", session.get("created_at", datetime.now()))
        duration = (datetime.now() - start).total_seconds()
        return {
            "totalMessagesExchanged": session.get("message_count", 0),
            "engagementDurationSeconds": round(duration, 2)
        }

    @property
    def active_session_count(self) -> int:
        """Get the count of active sessions."""
        self._cleanup_expired()
        return len(self.sessions)
