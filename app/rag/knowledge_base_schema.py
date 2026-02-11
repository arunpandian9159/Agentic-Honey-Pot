"""
Knowledge Base Schema for RAG system.
Pydantic models defining what data is stored in vector database.
"""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ConversationExample(BaseModel):
    """Complete conversation stored in RAG."""
    
    # Identifiers
    conversation_id: str
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Conversation content
    scammer_messages: List[str] = Field(default_factory=list)
    victim_responses: List[str] = Field(default_factory=list)
    full_conversation: str = ""  # For embedding
    
    # Metadata for filtering
    persona: str
    scam_type: str
    message_count: int = 0
    
    # Success metrics
    intelligence_extracted: Dict[str, List[str]] = Field(default_factory=dict)
    intelligence_score: float = 0.0  # 0-10
    engagement_quality: float = 0.0  # 0-10
    extraction_success: bool = False
    
    # Learning tags
    successful_tactics: List[str] = Field(default_factory=list)
    persona_consistency: float = 8.0  # 0-10
    human_likeness: float = 9.0  # 0-10


class ResponsePattern(BaseModel):
    """Individual successful response pattern."""
    
    pattern_id: str
    session_id: str
    persona: str
    scam_type: str
    
    # The response pair
    scammer_message: str
    victim_response: str
    conversation_stage: str = "engagement"  # initial, engagement, extraction
    
    # Success indicators
    led_to_intelligence: bool = False
    kept_engagement: bool = True
    maintained_persona: bool = True
    
    # Categorization
    tags: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)


class ExtractionTactic(BaseModel):
    """Successful intelligence extraction pattern."""
    
    tactic_id: str
    session_id: str
    scam_type: str
    persona: str
    
    # The tactic
    setup_messages: List[str] = Field(default_factory=list)
    extraction_question: str
    scammer_response: str
    
    # Results
    intelligence_type: str  # bank_account, upi_id, phishing_link, phone_number
    success_rate: float = 1.0  # Will average over time
    
    # Reusability
    generalized_pattern: str
    timestamp: datetime = Field(default_factory=datetime.now)
