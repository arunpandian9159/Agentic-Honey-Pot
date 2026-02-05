"""
Intelligence Data Model for AI Honeypot API.

Standardized model for extracted intelligence data.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class IntelligenceType(Enum):
    """Enum for different types of intelligence."""
    BANK_ACCOUNT = "bank_account"
    UPI_ID = "upi_id"
    PHONE_NUMBER = "phone_number"
    URL = "url"
    EMAIL = "email"
    CRYPTO_WALLET = "crypto_wallet"
    PERSONAL_INFO = "personal_info"
    OTHER = "other"


class IntelligenceConfidence(Enum):
    """Enum for intelligence extraction confidence."""
    LOW = 0.3
    MEDIUM = 0.6
    HIGH = 0.8
    VERY_HIGH = 0.95


@dataclass
class IntelligenceItem:
    """Individual intelligence item."""
    
    type: IntelligenceType
    value: str
    confidence: float
    context: str
    metadata: Dict[str, Any]
    extracted_at: datetime
    
    def __post_init__(self):
        """Validate the intelligence item."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        
        if not self.value or not self.value.strip():
            raise ValueError("Value cannot be empty")
    
    @property
    def confidence_level(self) -> IntelligenceConfidence:
        """Get confidence level."""
        if self.confidence >= 0.95:
            return IntelligenceConfidence.VERY_HIGH
        elif self.confidence >= 0.8:
            return IntelligenceConfidence.HIGH
        elif self.confidence >= 0.6:
            return IntelligenceConfidence.MEDIUM
        else:
            return IntelligenceConfidence.LOW
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type.value,
            "value": self.value,
            "confidence": self.confidence,
            "context": self.context,
            "metadata": self.metadata,
            "extracted_at": self.extracted_at.isoformat(),
            "confidence_level": self.confidence_level.name
        }


@dataclass
class IntelligenceData:
    """Complete intelligence extraction result."""
    
    items: List[IntelligenceItem]
    extraction_method: str
    confidence: float
    processing_time_ms: float
    metadata: Dict[str, Any]
    
    def __post_init__(self):
        """Validate the intelligence data."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        
        if self.processing_time_ms < 0:
            raise ValueError("Processing time cannot be negative")
    
    @property
    def total_items(self) -> int:
        """Get total number of intelligence items."""
        return len(self.items)
    
    @property
    def high_confidence_items(self) -> List[IntelligenceItem]:
        """Get items with high confidence (>= 0.8)."""
        return [item for item in self.items if item.confidence >= 0.8]
    
    @property
    def items_by_type(self) -> Dict[IntelligenceType, List[IntelligenceItem]]:
        """Get items grouped by type."""
        result = {}
        for item in self.items:
            if item.type not in result:
                result[item.type] = []
            result[item.type].append(item)
        return result
    
    def get_items_by_type(self, intelligence_type: IntelligenceType) -> List[IntelligenceItem]:
        """Get items of a specific type."""
        return [item for item in self.items if item.type == intelligence_type]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "items": [item.to_dict() for item in self.items],
            "extraction_method": self.extraction_method,
            "confidence": self.confidence,
            "processing_time_ms": self.processing_time_ms,
            "metadata": self.metadata,
            "total_items": self.total_items,
            "high_confidence_count": len(self.high_confidence_items)
        }
    
    @classmethod
    def empty(cls, extraction_method: str = "none") -> "IntelligenceData":
        """Create empty intelligence data."""
        return cls(
            items=[],
            extraction_method=extraction_method,
            confidence=0.0,
            processing_time_ms=0.0,
            metadata={}
        )


# Convenience functions for common intelligence types
def create_bank_account_intelligence(
    account_number: str,
    ifsc_code: Optional[str] = None,
    bank_name: Optional[str] = None,
    confidence: float = 0.8,
    context: str = ""
) -> IntelligenceItem:
    """Create bank account intelligence item."""
    metadata = {}
    if ifsc_code:
        metadata["ifsc_code"] = ifsc_code
    if bank_name:
        metadata["bank_name"] = bank_name
    
    return IntelligenceItem(
        type=IntelligenceType.BANK_ACCOUNT,
        value=account_number,
        confidence=confidence,
        context=context,
        metadata=metadata,
        extracted_at=datetime.utcnow()
    )


def create_upi_intelligence(
    upi_id: str,
    confidence: float = 0.8,
    context: str = ""
) -> IntelligenceItem:
    """Create UPI ID intelligence item."""
    return IntelligenceItem(
        type=IntelligenceType.UPI_ID,
        value=upi_id,
        confidence=confidence,
        context=context,
        metadata={},
        extracted_at=datetime.utcnow()
    )


def create_phone_intelligence(
    phone_number: str,
    confidence: float = 0.8,
    context: str = ""
) -> IntelligenceItem:
    """Create phone number intelligence item."""
    return IntelligenceItem(
        type=IntelligenceType.PHONE_NUMBER,
        value=phone_number,
        confidence=confidence,
        context=context,
        metadata={},
        extracted_at=datetime.utcnow()
    )