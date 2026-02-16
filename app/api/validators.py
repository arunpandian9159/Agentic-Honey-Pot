"""
Request and Response validators for AI Honeypot API.
Pydantic models for API data validation.
"""

import re
from typing import List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime

ALLOWED_SENDERS = {"scammer", "user"}
ALLOWED_CHANNELS = {"SMS", "WhatsApp", "Email", "Telegram", "Voice", "Web"}
ALLOWED_LANGUAGES = {"English", "Hindi", "Tamil", "Telugu", "Bengali", "Marathi", "Gujarati", "Kannada", "Malayalam"}
SESSION_ID_PATTERN = re.compile(r'^[a-zA-Z0-9\-_]{1,128}$')


class Message(BaseModel):
    """Single message in a conversation."""
    model_config = ConfigDict(populate_by_name=True)

    sender: str = Field(..., description="Message sender: 'scammer' or 'user'")
    text: str = Field(..., description="Message text content")
    timestamp: Union[str, int] = Field(..., description="Timestamp (ISO 8601 string or Unix ms)")

    @field_validator("sender")
    @classmethod
    def validate_sender(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in ALLOWED_SENDERS:
            raise ValueError(f"sender must be one of {ALLOWED_SENDERS}, got '{v}'")
        return v

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("text must not be empty")
        if len(v) > 5000:
            raise ValueError(f"text exceeds maximum length of 5000 characters ({len(v)})")
        return v


class Metadata(BaseModel):
    """Request metadata for context."""
    model_config = ConfigDict(populate_by_name=True)

    channel: Optional[str] = Field(default="SMS", description="Communication channel")
    language: Optional[str] = Field(default="English", description="Message language")
    locale: Optional[str] = Field(default="IN", description="Locale code")

    @field_validator("channel")
    @classmethod
    def validate_channel(cls, v: Optional[str]) -> Optional[str]:
        if v and v not in ALLOWED_CHANNELS:
            return "SMS"  # Graceful fallback to default
        return v

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: Optional[str]) -> Optional[str]:
        if v and v not in ALLOWED_LANGUAGES:
            return "English"  # Graceful fallback to default
        return v


class ChatRequest(BaseModel):
    """Request body for /api/chat endpoint."""
    model_config = ConfigDict(populate_by_name=True)

    sessionId: str = Field(..., description="Unique session identifier")
    message: Message = Field(..., description="Current message")
    conversationHistory: List[Message] = Field(
        default=[],
        description="Previous messages in conversation"
    )
    metadata: Optional[Metadata] = Field(
        default=None,
        description="Request metadata"
    )

    @field_validator("sessionId")
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("sessionId must not be empty")
        if not SESSION_ID_PATTERN.match(v):
            raise ValueError("sessionId must be 1-128 alphanumeric characters, hyphens, or underscores")
        return v


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

