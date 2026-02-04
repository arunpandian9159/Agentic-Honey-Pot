"""
Robustness tests for AI Honeypot API.
Verifies flexible request validation and dual response fields.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import os

# Set test environment variables
os.environ["API_SECRET_KEY"] = "test-api-key-12345"
os.environ["GROQ_API_KEY"] = "test-groq-key"
os.environ["ENVIRONMENT"] = "testing"

from main import app

client = TestClient(app)

class TestFlexibleValidation:
    """Tests for flexible request/response handling."""
    
    @patch('app.api.routes.optimized_agent.process_message', new_callable=AsyncMock)
    def test_camel_case_request(self, mock_process):
        """Should accept camelCase fields (sessionId, conversationHistory)."""
        mock_process.return_value = {
            "is_scam": False,
            "confidence": 0.1,
            "response": "Hello!",
            "scam_type": "none"
        }
        
        response = client.post(
            "/api/chat",
            headers={"x-api-key": "test-api-key-12345"},
            json={
                "sessionId": "camel-test-001",
                "message": {
                    "sender": "scammer",
                    "text": "hi",
                    "timestamp": 123456789
                },
                "conversationHistory": []
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
        assert "response" in data
        assert data["reply"] == "Hello!"
        assert data["response"] == "Hello!"

    @patch('app.api.routes.optimized_agent.process_message', new_callable=AsyncMock)
    def test_snake_case_request(self, mock_process):
        """Should accept snake_case fields (session_id, conversation_history) via aliases."""
        mock_process.return_value = {
            "is_scam": False,
            "confidence": 0.1,
            "response": "Snake response",
            "scam_type": "none"
        }
        
        response = client.post(
            "/api/chat",
            headers={"x-api-key": "test-api-key-12345"},
            json={
                "session_id": "snake-test-001",
                "message": {
                    "sender": "scammer",
                    "text": "hi",
                    "timestamp": 123456789
                },
                "conversation_history": []
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["reply"] == "Snake response"
        assert data["response"] == "Snake response"

    @patch('app.api.routes.optimized_agent.process_message', new_callable=AsyncMock)
    def test_mixed_case_request(self, mock_process):
        """Should accept mixed case fields."""
        mock_process.return_value = {
            "is_scam": False,
            "confidence": 0.1,
            "response": "Mixed response",
            "scam_type": "none"
        }
        
        response = client.post(
            "/api/chat",
            headers={"x-api-key": "test-api-key-12345"},
            json={
                "sessionId": "mixed-test-001",
                "message": {
                    "sender": "scammer",
                    "text": "hi",
                    "timestamp": 123456789
                },
                "conversation_history": []
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["reply"] == "Mixed response"
        assert data["response"] == "Mixed response"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
