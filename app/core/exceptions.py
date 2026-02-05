"""
Custom Exceptions for AI Honeypot API.

Standardized exception hierarchy for better error handling.
"""

from typing import Optional, Dict, Any


class HoneypotException(Exception):
    """Base exception for all honeypot errors."""
    
    def __init__(self, message: str, code: str = "GENERIC_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.message,
            "code": self.code,
            "details": self.details
        }


class ConfigurationError(HoneypotException):
    """Raised when there's a configuration issue."""
    
    def __init__(self, message: str, config_key: Optional[str] = None):
        super().__init__(
            message,
            code="CONFIG_ERROR",
            details={"config_key": config_key} if config_key else {}
        )


class LLMError(HoneypotException):
    """Raised when LLM operations fail."""
    
    def __init__(self, message: str, model: Optional[str] = None, error_type: Optional[str] = None):
        super().__init__(
            message,
            code="LLM_ERROR",
            details={"model": model, "error_type": error_type}
        )


class RateLimitError(HoneypotException):
    """Raised when rate limits are exceeded."""
    
    def __init__(self, message: str, retry_after: Optional[int] = None, limit_type: Optional[str] = None):
        super().__init__(
            message,
            code="RATE_LIMIT_ERROR",
            details={"retry_after": retry_after, "limit_type": limit_type}
        )


class DetectionError(HoneypotException):
    """Raised when scam detection fails."""
    
    def __init__(self, message: str, analyzer: Optional[str] = None):
        super().__init__(
            message,
            code="DETECTION_ERROR",
            details={"analyzer": analyzer}
        )


class ExtractionError(HoneypotException):
    """Raised when intelligence extraction fails."""
    
    def __init__(self, message: str, extraction_type: Optional[str] = None):
        super().__init__(
            message,
            code="EXTRACTION_ERROR",
            details={"extraction_type": extraction_type}
        )


class SessionError(HoneypotException):
    """Raised when session operations fail."""
    
    def __init__(self, message: str, session_id: Optional[str] = None):
        super().__init__(
            message,
            code="SESSION_ERROR",
            details={"session_id": session_id}
        )


class ValidationError(HoneypotException):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None):
        super().__init__(
            message,
            code="VALIDATION_ERROR",
            details={"field": field, "value": value}
        )


class AuthenticationError(HoneypotException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, code="AUTHENTICATION_ERROR")


class AuthorizationError(HoneypotException):
    """Raised when authorization fails."""
    
    def __init__(self, message: str = "Authorization failed"):
        super().__init__(message, code="AUTHORIZATION_ERROR")


class PersonaError(HoneypotException):
    """Raised when persona operations fail."""
    
    def __init__(self, message: str, persona_name: Optional[str] = None):
        super().__init__(
            message,
            code="PERSONA_ERROR",
            details={"persona_name": persona_name}
        )


class IntegrationError(HoneypotException):
    """Raised when external integrations fail."""
    
    def __init__(self, message: str, integration: Optional[str] = None):
        super().__init__(
            message,
            code="INTEGRATION_ERROR",
            details={"integration": integration}
        )