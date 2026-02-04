"""
Tests for Enhanced Scam Detection System.
Tests individual analyzers and the combined EnhancedScamDetector.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
import json

from app.detectors.linguistic_analyzer import LinguisticAnalyzer
from app.detectors.behavioral_analyzer import BehavioralAnalyzer
from app.detectors.technical_analyzer import TechnicalAnalyzer
from app.detectors.context_analyzer import ContextAnalyzer
from app.agents.enhanced_detector import EnhancedScamDetector
from tests.mock_data import SYNTHETIC_SCAM_MESSAGES, LEGITIMATE_MESSAGES


class TestLinguisticAnalyzer:
    """Tests for linguistic analysis."""
    
    def setup_method(self):
        self.analyzer = LinguisticAnalyzer()
    
    def test_detects_urgency_extreme(self):
        """Should detect extreme urgency language."""
        message = "URGENT! Act immediately or your account will be blocked TODAY!"
        result = self.analyzer.analyze(message)
        
        assert result["urgency_score"] > 0.5
        assert result["overall_linguistic_score"] > 0.3
    
    def test_detects_threats(self):
        """Should detect threatening language."""
        message = "Your account will be suspended and legal action will be taken."
        result = self.analyzer.analyze(message)
        
        assert result["threat_score"] > 0.3
    
    def test_detects_authority_impersonation(self):
        """Should detect authority claims."""
        message = "This is an official notification from RBI department."
        result = self.analyzer.analyze(message)
        
        assert result["authority_score"] > 0.3
    
    def test_detects_manipulation(self):
        """Should detect emotional manipulation."""
        message = "Congratulations! You won a special exclusive prize!"
        result = self.analyzer.analyze(message)
        
        assert result["manipulation_score"] > 0.3
    
    def test_low_score_for_normal_message(self):
        """Normal messages should have low scores."""
        message = "Hi, how are you doing today? Hope you're well."
        result = self.analyzer.analyze(message)
        
        assert result["overall_linguistic_score"] < 0.3


class TestBehavioralAnalyzer:
    """Tests for behavioral analysis."""
    
    def setup_method(self):
        self.analyzer = BehavioralAnalyzer()
    
    def test_detects_info_requests(self):
        """Should detect requests for personal information."""
        message = "Please share your password and OTP to verify your account."
        result = self.analyzer.analyze(message)
        
        assert result["information_request_score"] > 0.7
    
    def test_detects_payment_demands(self):
        """Should detect payment requests."""
        message = "Pay ₹500 processing fee to claim your prize. Transfer to this UPI."
        result = self.analyzer.analyze(message)
        
        assert result["payment_demand_score"] > 0.5
    
    def test_detects_time_pressure(self):
        """Should detect artificial time pressure."""
        message = "Act now within 24 hours or your account will expire today!"
        result = self.analyzer.analyze(message)
        
        assert result["time_pressure_score"] > 0.4
    
    def test_detects_secrecy(self):
        """Should detect secrecy requests."""
        message = "Don't tell anyone about this. Keep it confidential between us."
        result = self.analyzer.analyze(message)
        
        assert result["secrecy_score"] > 0.8


class TestTechnicalAnalyzer:
    """Tests for technical analysis."""
    
    def setup_method(self):
        self.analyzer = TechnicalAnalyzer()
    
    def test_extracts_urls(self):
        """Should extract URLs from message."""
        message = "Click here: https://example.com/verify?id=123"
        result = self.analyzer.analyze(message)
        
        assert len(result["urls_found"]) == 1
        assert "example.com" in result["urls_found"][0]
    
    def test_detects_link_shorteners(self):
        """Should flag link shorteners as suspicious."""
        message = "Click this link: https://bit.ly/verify-now"
        result = self.analyzer.analyze(message)
        
        assert result["domain_score"] > 0.5
    
    def test_detects_suspicious_tlds(self):
        """Should flag suspicious TLDs."""
        message = "Verify at: https://bank-secure.xyz/login"
        result = self.analyzer.analyze(message)
        
        assert result["domain_score"] > 0.5
    
    def test_no_urls_zero_score(self):
        """Should return zero score when no URLs present."""
        message = "Hello, how are you doing today?"
        result = self.analyzer.analyze(message)
        
        assert result["overall_technical_score"] == 0.0


class TestContextAnalyzer:
    """Tests for context analysis."""
    
    def setup_method(self):
        self.analyzer = ContextAnalyzer()
    
    def test_first_message_urgent_suspicious(self):
        """First message with urgency should be suspicious."""
        message = "URGENT: Your account is blocked! Verify immediately!"
        result = self.analyzer.analyze(message, {}, [])
        
        assert result["expected_communication_score"] > 0.6
    
    def test_sensitive_via_sms_suspicious(self):
        """Sensitive requests via SMS should be suspicious."""
        message = "Please share your password to verify."
        metadata = {"channel": "sms"}
        result = self.analyzer.analyze(message, metadata, [])
        
        assert result["channel_score"] > 0.7


class TestEnhancedScamDetector:
    """Tests for the combined EnhancedScamDetector."""
    
    @pytest.fixture
    def mock_llm(self):
        mock = AsyncMock()
        mock.generate_json.return_value = json.dumps({
            "is_scam": True,
            "confidence": 0.85,
            "scam_type": "bank_fraud",
            "reasoning": "Message shows multiple scam indicators",
            "red_flags": ["urgency", "threats"],
            "legitimacy_signals": [],
            "factors": {
                "linguistic": 0.8,
                "behavioral": 0.7,
                "technical": 0.5,
                "legitimacy": 0.2
            }
        })
        return mock
    
    @pytest.mark.asyncio
    async def test_detects_obvious_scam(self, mock_llm):
        """Should detect obvious scam messages."""
        detector = EnhancedScamDetector(mock_llm)
        
        message = "URGENT! Your SBI account will be blocked. Send OTP to 9876543210 immediately!"
        result = await detector.analyze(message, {"channel": "sms"})
        
        assert result["is_scam"] is True
        assert result["confidence"] > 0.6
        assert result["scam_type"] == "bank_fraud"
        assert len(result["red_flags"]) > 0
    
    @pytest.mark.asyncio
    async def test_returns_factor_scores(self, mock_llm):
        """Should return detailed factor scores."""
        detector = EnhancedScamDetector(mock_llm)
        
        message = "Your account is suspended. Pay fee to restore."
        result = await detector.analyze(message)
        
        assert "factor_scores" in result
        assert "linguistic" in result["factor_scores"]
        assert "behavioral" in result["factor_scores"]
        assert "technical" in result["factor_scores"]
    
    @pytest.mark.asyncio
    async def test_handles_llm_failure(self, mock_llm):
        """Should handle LLM failure gracefully."""
        mock_llm.generate_json.side_effect = Exception("API Error")
        detector = EnhancedScamDetector(mock_llm)
        
        message = "Your account is blocked!"
        result = await detector.analyze(message)
        
        # Should return fallback result
        assert "is_scam" in result
        assert "confidence" in result


class TestEnhancedDetectorOnMockData:
    """Test detector on synthetic scam messages."""
    
    @pytest.fixture
    def mock_llm(self):
        """Mock LLM that returns scam detection."""
        mock = AsyncMock()
        mock.generate_json.return_value = json.dumps({
            "is_scam": True,
            "confidence": 0.8,
            "scam_type": "bank_fraud",
            "reasoning": "Detected scam patterns",
            "red_flags": ["urgency"],
            "legitimacy_signals": [],
            "factors": {}
        })
        return mock
    
    def test_analyzers_score_scam_messages_high(self):
        """Individual analyzers should score scam messages high."""
        linguistic = LinguisticAnalyzer()
        behavioral = BehavioralAnalyzer()
        technical = TechnicalAnalyzer()        
        passed = 0
        total = 0
        
        for scam_type, messages in SYNTHETIC_SCAM_MESSAGES.items():
            for msg_data in messages[:2]:  # Test first 2 of each type
                message = msg_data["message"]
                total += 1
                
                ling_result = linguistic.analyze(message)
                behav_result = behavioral.analyze(message)
                tech_result = technical.analyze(message)
                
                # Combine all analyzer scores
                combined = (
                    ling_result["overall_linguistic_score"] + 
                    behav_result["overall_behavioral_score"] +
                    tech_result["overall_technical_score"]
                )
                
                if combined > 0.1:  # At least one analyzer should detect something
                    passed += 1
        
        # Allow 80% detection rate for rule-based analyzers (LLM handles rest)
        detection_rate = passed / total if total > 0 else 0
        assert detection_rate >= 0.8, f"Detection rate {detection_rate:.2f} below 0.8"

    
    def test_analyzers_score_legitimate_low(self):
        """Individual analyzers should score legitimate messages low."""
        linguistic = LinguisticAnalyzer()
        behavioral = BehavioralAnalyzer()
        
        for msg_data in LEGITIMATE_MESSAGES:
            message = msg_data["message"]
            
            ling_result = linguistic.analyze(message)
            behav_result = behavioral.analyze(message)
            
            combined = ling_result["overall_linguistic_score"] + behav_result["overall_behavioral_score"]
            # Legitimate messages should have low combined score
            assert combined < 0.6, f"False positive on: {message}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
