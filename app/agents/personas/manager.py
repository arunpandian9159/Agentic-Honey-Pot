"""
Persona Management System for AI Honeypot API.
Orchestrates individual persona implementations.
"""

import random
import logging
from typing import Dict, List, Optional, Type

from app.agents.personas.base_persona import BasePersona
from app.agents.personas.elderly_confused import ElderlyConfused
from app.agents.personas.busy_professional import BusyProfessional
from app.agents.personas.curious_student import CuriousStudent
from app.agents.personas.tech_naive_parent import TechNaiveParent
from app.agents.personas.desperate_job_seeker import DesperateJobSeeker

logger = logging.getLogger(__name__)


class PersonaManager:
    """Manages and selects victim personas."""
    
    def __init__(self):
        self._personas: Dict[str, BasePersona] = {
            "elderly_confused": ElderlyConfused(),
            "busy_professional": BusyProfessional(),
            "curious_student": CuriousStudent(),
            "tech_naive_parent": TechNaiveParent(),
            "desperate_job_seeker": DesperateJobSeeker()
        }

    def select_persona(
        self,
        scam_type: str,
        urgency: str = "medium"
    ) -> str:
        """
        Select an appropriate persona based on scam type and urgency.
        """
        matching_personas = [
            name for name, persona in self._personas.items()
            if persona.should_respond_to_scam_type(scam_type)
        ]
        
        if not matching_personas:
            logger.info(f"No matching personas for {scam_type}, using defaults")
            matching_personas = ["tech_naive_parent", "busy_professional"]
        
        # Heuristics for selection
        if urgency in ["critical", "high"]:
            if "elderly_confused" in matching_personas:
                selected = "elderly_confused"
            elif "tech_naive_parent" in matching_personas:
                selected = "tech_naive_parent"
            else:
                selected = random.choice(matching_personas)
        else:
            selected = random.choice(matching_personas)
            
        logger.info(f"Selected persona '{selected}' for scam_type={scam_type}")
        return selected

    def get_persona_prompt(self, persona_name: str) -> str:
        """Get the system prompt for a specific persona."""
        persona = self._personas.get(persona_name, self._personas["tech_naive_parent"])
        return persona.get_system_prompt()

    def get_persona_details(self, persona_name: str) -> Optional[Dict]:
        """Get persona details (backward compatibility)."""
        persona = self._personas.get(persona_name)
        if not persona:
            return None
            
        return {
            "name": persona.name,
            "display_name": persona.display_name,
            "age": persona.age_range,
            "tech_skill": persona.tech_skill_level,
            "trust_level": persona.trust_level,
            "characteristics": persona.get_characteristics(),
            "scam_types": persona.get_supported_scam_types(),
            "system_prompt": persona.get_system_prompt()
        }

    def list_personas(self) -> List[str]:
        """List all available persona names."""
        return list(self._personas.keys())
    
    def apply_variation(self, persona_name: str, response: str, context: Dict) -> str:
        """Apply persona-specific variations to a response."""
        persona = self._personas.get(persona_name)
        if not persona:
            return response
        return persona.generate_response_variation(response, context)
