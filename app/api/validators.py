"""
Request and Response validators for AI Honeypot API.
Pydantic models for API data validation.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class Message(BaseModel):
    """Single message in a conversation."""
    model_config = ConfigDict(populate_by_name=True)
    
    sender: str = Field(..., description="Message sender: 'scammer' or 'user'")
    text: str = Field(..., description="Message text content")
    timestamp: int = Field(..., description="Unix timestamp in milliseconds")


class Metadata(BaseModel):
    """Request metadata for context."""
    model_config = ConfigDict(populate_by_name=True)
    
    channel: Optional[str] = Field(default="SMS", description="Communication channel")
    language: Optional[str] = Field(default="English", description="Message language")
    locale: Optional[str] = Field(default="IN", description="Locale code")


class ChatRequest(BaseModel):
    """Request body for /api/chat endpoint."""
    model_config = ConfigDict(populate_by_name=True)
    
    sessionId: str = Field(..., alias="session_id", description="Unique session identifier")
    message: Message = Field(..., description="Current message")
    conversationHistory: List[Message] = Field(
        default=[], 
        alias="conversation_history",
        description="Previous messages in conversation"
    )
    metadata: Optional[Metadata] = Field(
        default=None,
        description="Request metadata"
    )


class ChatResponse(BaseModel):
    """Response body for /api/chat endpoint."""
    model_config = ConfigDict(populate_by_name=True)
    
    status: str = Field(..., description="Response status: 'success' or 'error'")
    reply: str = Field(..., description="Agent's reply message")
    response: str = Field(..., description="Alias for reply for compatibility")


class HealthResponse(BaseModel):
    """Response body for /health endpoint."""
    status: str = Field(default="healthy", description="Service status")
    active_sessions: int = Field(..., description="Number of active sessions")
    timestamp: str = Field(..., description="Current timestamp")
    groq_requests: Optional[int] = Field(default=None, description="Total Groq API requests")


class MetricsResponse(BaseModel):
    """Response body for /metrics endpoint."""
    total_sessions: int = Field(default=0)
    scams_detected: int = Field(default=0)
    average_messages_per_session: float = Field(default=0.0)
    total_intelligence_extracted: int = Field(default=0)
    groq_requests: int = Field(default=0)


class ErrorResponse(BaseModel):
    """Error response body."""
    status: str = Field(default="error")
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(default=None, description="Error details")
