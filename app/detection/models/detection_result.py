"""
Detection Result Model for AI Honeypot API.

Standardized model for scam detection results.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class ScamType(Enum):
    """Enum for different types of scams."""
    BANK_FRAUD = "bank_fraud"
    UPI_FRAUD = "upi_fraud"
    PHISHING = "phishing"
    TECH_SUPPORT = "tech_support"
    LOTTERY = "lottery"
    JOB_OFFER = "job_offer"
    ROMANCE = "romance"
    INVESTMENT = "investment"
    OTHER = "other"


class DetectionConfidence(Enum):
    """Enum for detection confidence levels."""
    VERY_LOW = 0.0
    LOW = 0.25
    MEDIUM = 0.5
    HIGH = 0.75
    VERY_HIGH = 1.0


@dataclass
class DetectionResult:
    """Standardized detection result."""
    
    is_scam: bool
    confidence: float
    scam_type: Optional[ScamType]
    reasoning: str
    red_flags: List[str]
    legitimacy_signals: List[str]
    factors: Dict[str, Any]
    analyzer_results: Dict[str, Any]
    
    def __post_init__(self):
        """Validate the detection result."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        
        if self.is_scam and self.scam_type is None:
            raise ValueError("Scam type must be specified when is_scam is True")
    
    @property
    def confidence_level(self) -> DetectionConfidence:
        """Get confidence level enum."""
        if self.confidence >= 0.9:
            return DetectionConfidence.VERY_HIGH
        elif self.confidence >= 0.7:
            return DetectionConfidence.HIGH
        elif self.confidence >= 0.4:
            return DetectionConfidence.MEDIUM
        elif self.confidence >= 0.2:
            return DetectionConfidence.LOW
        else:
            return DetectionConfidence.VERY_LOW
    
    @property
    def risk_level(self) -> str:
        """Get human-readable risk level."""
        if self.confidence >= 0.8:
            return "VERY_HIGH"
        elif self.confidence >= 0.6:
            return "HIGH"
        elif self.confidence >= 0.4:
            return "MEDIUM"
        elif self.confidence >= 0.2:
            return "LOW"
        else:
            return "VERY_LOW"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_scam": self.is_scam,
            "confidence": self.confidence,
            "scam_type": self.scam_type.value if self.scam_type else None,
            "reasoning": self.reasoning,
            "red_flags": self.red_flags,
            "legitimacy_signals": self.legitimacy_signals,
            "factors": self.factors,
            "analyzer_results": self.analyzer_results,
            "confidence_level": self.confidence_level.name,
            "risk_level": self.risk_level
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DetectionResult":
        """Create from dictionary."""
        scam_type = None
        if data.get("scam_type"):
            scam_type = ScamType(data["scam_type"])
        
        return cls(
            is_scam=data["is_scam"],
            confidence=data["confidence"],
            scam_type=scam_type,
            reasoning=data["reasoning"],
            red_flags=data.get("red_flags", []),
            legitimacy_signals=data.get("legitimacy_signals", []),
            factors=data.get("factors", {}),
            analyzer_results=data.get("analyzer_results", {})
        )


@dataclass
class AnalyzerResult:
    """Result from individual analyzer."""
    
    analyzer_name: str
    is_scam: bool
    confidence: float
    reasoning: str
    details: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "analyzer_name": self.analyzer_name,
            "is_scam": self.is_scam,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "details": self.details
        }