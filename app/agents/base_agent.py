"""
Base Agent Interface for AI Honeypot API.

Defines the contract that all agent implementations must follow.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any


class AgentInterface(ABC):
    """Abstract base class for all honeypot agents."""
    
    @abstractmethod
    async def process_message(
        self,
        message: str,
        session: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a scammer message and return response.
        
        Args:
            message: The scammer's message
            session: Session data including conversation history
            metadata: Additional metadata about the message
            
        Returns:
            Dictionary containing:
                - response: str - The agent's response
                - detection_result: Dict - Scam detection results
                - intelligence: Dict - Extracted intelligence
                - persona_used: str - Persona identifier
                - confidence: float - Confidence in response
        """
        pass
    
    @abstractmethod
    async def reset_session(self, session_id: str) -> None:
        """Reset agent state for a new session."""
        pass
    
    @property
    @abstractmethod
    def agent_type(self) -> str:
        """Return the type of agent."""
        pass
    
    @property
    @abstractmethod
    def capabilities(self) -> list[str]:
        """Return list of agent capabilities."""
        pass


class BaseAgent(AgentInterface):
    """Base implementation with common functionality."""
    
    def __init__(self, name: str, capabilities: list[str]):
        self._name = name
        self._capabilities = capabilities
        self._session_states = {}
    
    @property
    def agent_type(self) -> str:
        return self._name
    
    @property
    def capabilities(self) -> list[str]:
        return self._capabilities.copy()
    
    async def reset_session(self, session_id: str) -> None:
        """Reset session state."""
        if session_id in self._session_states:
            del self._session_states[session_id]
    
    def _get_session_state(self, session_id: str) -> Dict[str, Any]:
        """Get or create session state."""
        if session_id not in self._session_states:
            self._session_states[session_id] = {
                "message_count": 0,
                "persona": None,
                "context": {}
            }
        return self._session_states[session_id]
    
    def _update_session_state(self, session_id: str, updates: Dict[str, Any]) -> None:
        """Update session state."""
        state = self._get_session_state(session_id)
        state.update(updates)