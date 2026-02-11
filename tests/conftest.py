"""
Shared pytest fixtures for AI Honeypot test suite.
"""

import pytest
from app.agents.personas import PersonaManager


@pytest.fixture
def persona_manager():
    return PersonaManager()


@pytest.fixture
def empty_session():
    """Create a fresh session dict matching SessionManager.get_or_create()."""
    return {
        "session_id": "test-session",
        "message_count": 0,
        "scam_detected": False,
        "scam_confidence": 0.0,
        "scam_type": None,
        "persona": None,
        "conversation_history": [],
        "intelligence": {
            "bank_accounts": [],
            "upi_ids": [],
            "phone_numbers": [],
            "phishing_links": [],
            "suspicious_keywords": [],
        },
        "callback_sent": False,
    }
