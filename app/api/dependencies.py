"""
Dependency Injection System for AI Honeypot API.

Manages application dependencies and service locator pattern.
"""

from typing import Optional, Protocol
from functools import lru_cache

from app.core.config import settings
from app.llm.client import GroqClient
from app.agents.base_agent import AgentInterface
from app.agents.conversation_manager import ConversationManager
from app.detection.detector import ScamDetector
from app.intelligence.extractor import IntelligenceExtractor


class ContainerProtocol(Protocol):
    """Protocol for dependency container."""
    
    @property
    def llm_client(self) -> GroqClient:
        """Get LLM client instance."""
        ...
    
    @property
    def agent_service(self) -> AgentInterface:
        """Get agent service instance."""
        ...
    
    @property
    def detection_service(self) -> ScamDetector:
        """Get detection service instance."""
        ...
    
    @property
    def intelligence_service(self) -> IntelligenceExtractor:
        """Get intelligence extraction service instance."""
        ...


class DependencyContainer:
    """Dependency injection container."""
    
    def __init__(self):
        self._llm_client: Optional[GroqClient] = None
        self._agent_service: Optional[AgentInterface] = None
        self._detection_service: Optional[ScamDetector] = None
        self._intelligence_service: Optional[IntelligenceExtractor] = None
        self._conversation_manager: Optional[ConversationManager] = None
    
    @property
    def llm_client(self) -> GroqClient:
        """Get LLM client instance (singleton)."""
        if self._llm_client is None:
            self._llm_client = GroqClient(
                api_key=settings.GROQ_API_KEY,
                model=settings.LLM_MODEL
            )
        return self._llm_client
    
    @property
    def detection_service(self) -> ScamDetector:
        """Get detection service instance (singleton)."""
        if self._detection_service is None:
            self._detection_service = ScamDetector(
                llm_client=self.llm_client
            )
        return self._detection_service
    
    @property
    def intelligence_service(self) -> IntelligenceExtractor:
        """Get intelligence extraction service instance (singleton)."""
        if self._intelligence_service is None:
            self._intelligence_service = IntelligenceExtractor(
                llm_client=self.llm_client
            )
        return self._intelligence_service
    
    @property
    def conversation_manager(self) -> ConversationManager:
        """Get conversation manager instance (singleton)."""
        if self._conversation_manager is None:
            self._conversation_manager = ConversationManager(
                detection_service=self.detection_service,
                intelligence_service=self.intelligence_service
            )
        return self._conversation_manager
    
    def reset(self) -> None:
        """Reset all singleton instances."""
        self._llm_client = None
        self._agent_service = None
        self._detection_service = None
        self._intelligence_service = None
        self._conversation_manager = None


# Global container instance
_container = DependencyContainer()


@lru_cache()
def get_container() -> DependencyContainer:
    """Get the global dependency container."""
    return _container


# Convenience functions for FastAPI dependencies
def get_llm_client() -> GroqClient:
    """Get LLM client for dependency injection."""
    return get_container().llm_client


def get_detection_service() -> ScamDetector:
    """Get detection service for dependency injection."""
    return get_container().detection_service


def get_intelligence_service() -> IntelligenceExtractor:
    """Get intelligence service for dependency injection."""
    return get_container().intelligence_service


def get_conversation_manager() -> ConversationManager:
    """Get conversation manager for dependency injection."""
    return get_container().conversation_manager
