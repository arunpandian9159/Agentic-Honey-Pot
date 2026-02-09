"""
API endpoint tests for AI Honeypot API.
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


class TestHealthEndpoint:
    """Tests for /health endpoint."""
    
    def test_health_check_returns_200(self):
        """Health check should return 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_health_check_structure(self):
        """Health check should return correct structure."""
        response = client.get("/health")
        data = response.json()
        
        assert "status" in data
        assert "active_sessions" in data
        assert "timestamp" in data
        assert data["status"] == "healthy"
        assert isinstance(data["active_sessions"], int)


class TestRootEndpoint:
    """Tests for root endpoint."""
    
    def test_root_returns_200(self):
        """Root endpoint should return HTML dashboard."""
        response = client.get("/")
        assert response.status_code == 200
        # Should be HTML not JSON
        assert "text/html" in response.headers["content-type"]


class TestChatEndpointAuth:
    """Tests for /api/chat authentication."""
    
    def test_chat_without_api_key_returns_422(self):
        """Request without API key should fail."""
        response = client.post(
            "/api/chat",
            json={
                "sessionId": "test-001",
                "message": {
                    "sender": "scammer",
                    "text": "Your account is blocked",
                    "timestamp": 1234567890000
                }
            }
        )
        # FastAPI returns 422 for missing required header
        assert response.status_code == 422
    
    def test_chat_with_invalid_api_key_returns_401(self):
        """Request with invalid API key should return 401."""
        response = client.post(
            "/api/chat",
            headers={"x-api-key": "wrong-key"},
            json={
                "sessionId": "test-001",
                "message": {
                    "sender": "scammer",
                    "text": "Your account is blocked",
                    "timestamp": 1234567890000
                }
            }
        )
        assert response.status_code == 401
    
    def test_chat_with_valid_api_key_returns_200(self):
        """Request with valid API key should be processed."""
        with patch('app.api.routes.optimized_agent.process_message', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = {
                "is_scam": False,
                "confidence": 0.3,
                "scam_type": "other",
                "intel": {},
                "response": "Hello!"
            }
            
            response = client.post(
                "/api/chat",
                headers={"x-api-key": "test-api-key-12345"},
                json={
                    "sessionId": "test-001",
                    "message": {
                        "sender": "scammer",
                        "text": "Hello, how are you?",
                        "timestamp": 1234567890000
                    },
                    "conversationHistory": []
                }
            )
            
            assert response.status_code == 200


class TestChatEndpointValidation:
    """Tests for /api/chat request validation."""
    
    def test_chat_missing_session_id_fails(self):
        """Request without sessionId should fail validation."""
        response = client.post(
            "/api/chat",
            headers={"x-api-key": "test-api-key-12345"},
            json={
                "message": {
                    "sender": "scammer",
                    "text": "Test message",
                    "timestamp": 1234567890000
                }
            }
        )
        assert response.status_code == 422
    
    def test_chat_missing_message_fails(self):
        """Request without message should fail validation."""
        response = client.post(
            "/api/chat",
            headers={"x-api-key": "test-api-key-12345"},
            json={
                "sessionId": "test-001"
            }
        )
        assert response.status_code == 422
    
    def test_chat_invalid_message_structure_fails(self):
        """Request with invalid message structure should fail."""
        response = client.post(
            "/api/chat",
            headers={"x-api-key": "test-api-key-12345"},
            json={
                "sessionId": "test-001",
                "message": {
                    "text": "Missing sender and timestamp"
                }
            }
        )
        assert response.status_code == 422


class TestChatEndpointFlow:
    """Tests for /api/chat conversation flow."""
    
    @patch('app.api.routes.optimized_agent.process_message', new_callable=AsyncMock)
    def test_scam_detection_triggers_persona(
        self, mock_process
    ):
        """Detected scam should trigger response generation."""
        mock_process.return_value = {
            "is_scam": True,
            "confidence": 0.85,
            "scam_type": "bank_fraud",
            "intel": {
                "bank_accounts": [],
                "upi_ids": [],
                "phone_numbers": [],
                "links": []
            },
            "response": "Oh dear, my account is blocked? What should I do?"
        }
        
        response = client.post(
            "/api/chat",
            headers={"x-api-key": "test-api-key-12345"},
            json={
                "sessionId": "test-scam-001",
                "message": {
                    "sender": "scammer",
                    "text": "Your bank account is blocked. Verify immediately.",
                    "timestamp": 1234567890000
                },
                "conversationHistory": []
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["reply"]) > 0
    
    @patch('app.api.routes.optimized_agent.process_message', new_callable=AsyncMock)
    def test_non_scam_returns_neutral_response(self, mock_process):
        """Non-scam message should get neutral response."""
        mock_process.return_value = {
            "is_scam": False,
            "confidence": 0.2,
            "scam_type": "other",
            "intel": {},
            "response": "Tell me more please."
        }
        
        response = client.post(
            "/api/chat",
            headers={"x-api-key": "test-api-key-12345"},
            json={
                "sessionId": "test-legit-001",
                "message": {
                    "sender": "scammer",
                    "text": "Hello, how are you today?",
                    "timestamp": 1234567890000
                },
                "conversationHistory": []
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "tell me more" in data["reply"].lower() or "please" in data["reply"].lower()


class TestMetricsEndpoint:
    """Tests for /metrics endpoint."""
    
    def test_metrics_returns_200(self):
        """Metrics endpoint should return 200."""
        response = client.get("/metrics")
        assert response.status_code == 200
    
    def test_metrics_structure(self):
        """Metrics should have correct structure."""
        response = client.get("/metrics")
        data = response.json()
        
        assert "total_sessions" in data
        assert "scams_detected" in data
        assert "groq_requests" in data
        assert isinstance(data["total_sessions"], int)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
