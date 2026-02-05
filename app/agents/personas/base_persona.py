"""
Base Persona Interface for AI Honeypot API.

Defines the contract that all persona implementations must follow.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class BasePersona(ABC):
    """Abstract base class for all victim personas."""
    
    def __init__(self, name: str, display_name: str, config: Dict[str, Any]):
        self.name = name
        self.display_name = display_name
        self.config = config
        self._characteristics = config.get("characteristics", [])
        self._scam_types = config.get("scam_types", [])
        self._system_prompt = config.get("system_prompt", "")
    
    @property
    @abstractmethod
    def age_range(self) -> str:
        """Return the age range for this persona."""
        pass
    
    @property
    @abstractmethod
    def tech_skill_level(self) -> str:
        """Return technical skill level (very_low, low, medium, high)."""
        pass
    
    @property
    @abstractmethod
    def trust_level(self) -> str:
        """Return default trust level (very_low, low, medium, high)."""
        pass
    
    @abstractmethod
    def get_system_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Get the system prompt for this persona.
        
        Args:
            context: Optional context about the conversation
            
        Returns:
            System prompt string
        """
        pass
    
    @abstractmethod
    def should_respond_to_scam_type(self, scam_type: str) -> bool:
        """
        Determine if this persona should respond to a specific scam type.
        
        Args:
            scam_type: Type of scam detected
            
        Returns:
            True if persona should handle this scam type
        """
        pass
    
    @abstractmethod
    def generate_response_variation(self, base_response: str, context: Dict[str, Any]) -> str:
        """
        Generate a response variation based on persona characteristics.
        
        Args:
            base_response: The base response to modify
            context: Conversation context
            
        Returns:
            Modified response with persona characteristics
        """
        pass
    
    def get_characteristics(self) -> List[str]:
        """Get persona characteristics."""
        return self._characteristics.copy()
    
    def get_supported_scam_types(self) -> List[str]:
        """Get list of scam types this persona can handle."""
        return self._scam_types.copy()
    
    def __str__(self) -> str:
        return f"{self.display_name} ({self.name})"
    
    def __repr__(self) -> str:
        return f"BasePersona(name='{self.name}', display_name='{self.display_name}')"