"""
Scam Detector tests for AI Honeypot API.
"""

import pytest
from unittest.mock import AsyncMock, patch
import json

from app.agents.detector import ScamDetector
from tests.mock_data import SYNTHETIC_SCAM_MESSAGES, LEGITIMATE_MESSAGES


class TestScamDetectorFallback:
    """Tests for fallback keyword-based detection."""
    
    def setup_method(self):
        """Setup test fixtures."""
        mock_llm = AsyncMock()
        self.detector = ScamDetector(mock_llm)
    
    def test_fallback_detects_bank_fraud(self):
        """Fallback should detect bank fraud keywords."""
        message = "URGENT: Your bank account is suspended. Verify immediately or pay penalty."
        result = self.detector._fallback_detection(message)
        
        assert result["is_scam"] is True
        assert result["confidence"] > 0.5
        # Should detect multiple keywords like "urgent", "suspended", "verify immediately"
        assert len(result["key_indicators"]) >= 2
    
    def test_fallback_detects_upi_keywords(self):
        """Fallback should detect UPI fraud keywords."""
        message = "URGENT: Send money to this UPI ID immediately to claim your prize before account is blocked."
        result = self.detector._fallback_detection(message)
        
        assert result["is_scam"] is True
        assert "upi" in result["key_indicators"] or "urgent" in result["key_indicators"]
    
    def test_fallback_handles_legitimate_message(self):
        """Fallback should not flag legitimate messages."""
        message = "How are you doing today?"
        result = self.detector._fallback_detection(message)
        
        assert result["is_scam"] is False
        assert result["confidence"] < 0.5
    
    def test_fallback_confidence_scales_with_matches(self):
        """More keyword matches should increase confidence."""
        low_match = "Update your account."
        high_match = "URGENT: Your account is blocked! Verify immediately or pay penalty. Transfer money now!"
        
        low_result = self.detector._fallback_detection(low_match)
        high_result = self.detector._fallback_detection(high_match)
        
        assert high_result["confidence"] > low_result["confidence"]


class TestScamDetectorLLM:
    """Tests for LLM-based detection."""
    
    @pytest.mark.asyncio
    async def test_analyze_parses_valid_json(self):
        """Analyze should parse valid LLM JSON response."""
        mock_llm = AsyncMock()
        mock_llm.generate_json.return_value = json.dumps({
            "is_scam": True,
            "confidence": 0.9,
            "scam_type": "bank_fraud",
            "urgency_level": "high",
            "key_indicators": ["account blocked", "verify"]
        })
        
        detector = ScamDetector(mock_llm)
        result = await detector.analyze("Your account is blocked")
        
        assert result["is_scam"] is True
        assert result["confidence"] == 0.9
        assert result["scam_type"] == "bank_fraud"
    
    @pytest.mark.asyncio
    async def test_analyze_falls_back_on_invalid_json(self):
        """Analyze should use fallback if LLM returns invalid JSON."""
        mock_llm = AsyncMock()
        mock_llm.generate_json.side_effect = Exception("API Error")
        
        detector = ScamDetector(mock_llm)
        result = await detector.analyze("Your account is blocked. Verify now.")
        
        # Should fall back to keyword detection
        assert "is_scam" in result
        assert "confidence" in result


class TestScamDetectorOnMockData:
    """Test detector on synthetic scam messages."""
    
    def setup_method(self):
        """Setup test fixtures."""
        mock_llm = AsyncMock()
        self.detector = ScamDetector(mock_llm)
    
    def test_bank_fraud_detection_rate(self):
        """Should detect most bank fraud messages."""
        messages = SYNTHETIC_SCAM_MESSAGES.get("bank_fraud", [])
        detected = 0
        
        for msg_data in messages:
            result = self.detector._fallback_detection(msg_data["message"])
            if result["is_scam"]:
                detected += 1
        
        detection_rate = detected / len(messages) if messages else 0
        # Fallback detection rate can be lower - LLM is primary detector
        assert detection_rate >= 0.6, f"Bank fraud fallback detection rate: {detection_rate}"
    
    def test_upi_fraud_detection_rate(self):
        """Should detect most UPI fraud messages."""
        messages = SYNTHETIC_SCAM_MESSAGES.get("upi_fraud", [])
        detected = 0
        
        for msg_data in messages:
            result = self.detector._fallback_detection(msg_data["message"])
            if result["is_scam"]:
                detected += 1
        
        detection_rate = detected / len(messages) if messages else 0
        # Fallback detection rate can be lower - LLM is primary detector
        assert detection_rate >= 0.5, f"UPI fraud fallback detection rate: {detection_rate}"
    
    def test_legitimate_messages_not_flagged(self):
        """Should not flag legitimate messages as scams."""
        false_positives = 0
        
        for msg_data in LEGITIMATE_MESSAGES:
            result = self.detector._fallback_detection(msg_data["message"])
            if result["is_scam"]:
                false_positives += 1
        
        false_positive_rate = false_positives / len(LEGITIMATE_MESSAGES) if LEGITIMATE_MESSAGES else 0
        assert false_positive_rate <= 0.2, f"False positive rate: {false_positive_rate}"
    
    def test_overall_detection_accuracy(self):
        """Test overall detection accuracy across all scam types."""
        total_scams = 0
        detected_scams = 0
        
        for scam_type, messages in SYNTHETIC_SCAM_MESSAGES.items():
            for msg_data in messages:
                total_scams += 1
                result = self.detector._fallback_detection(msg_data["message"])
                if result["is_scam"]:
                    detected_scams += 1
        
        accuracy = detected_scams / total_scams if total_scams else 0
        # Fallback accuracy is lower - LLM handles most detection
        assert accuracy >= 0.5, f"Overall fallback detection accuracy: {accuracy}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
