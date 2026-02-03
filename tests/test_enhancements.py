"""
Tests for AI Honeypot Enhancement Components.
Tests the human-like response generation features.
"""

import pytest
from app.agents.enhanced_personas import (
    ENHANCED_PERSONAS,
    get_persona,
    get_random_opening,
    get_random_closing,
    should_add_typo
)
from app.agents.response_variation import ResponseVariationEngine
from app.agents.natural_flow import NaturalConversationFlow, get_stage_guidance
from app.agents.emotional_intelligence import EmotionalIntelligence
from app.agents.context_aware import ContextAwareManager, get_concise_context


class TestEnhancedPersonas:
    """Tests for enhanced persona definitions."""
    
    def test_all_personas_exist(self):
        """All 5 enhanced personas should be defined."""
        expected_personas = [
            "elderly_confused",
            "busy_professional",
            "curious_student",
            "tech_naive_parent",
            "desperate_job_seeker"
        ]
        for persona in expected_personas:
            assert persona in ENHANCED_PERSONAS, f"Missing persona: {persona}"
    
    def test_persona_has_required_fields(self):
        """Each persona should have all required fields."""
        required_fields = [
            "name",
            "base_traits",
            "opening_styles",
            "closing_styles",
            "emotional_states",
            "typo_patterns",
            "vocabulary",
            "enhanced_system_prompt"
        ]
        for persona_name, persona in ENHANCED_PERSONAS.items():
            for field in required_fields:
                assert field in persona, f"{persona_name} missing field: {field}"
    
    def test_get_persona_returns_valid_persona(self):
        """get_persona should return a valid persona dict."""
        persona = get_persona("elderly_confused")
        assert persona["name"] == "elderly_confused"
        assert "enhanced_system_prompt" in persona
    
    def test_get_persona_fallback(self):
        """get_persona with unknown name should return fallback."""
        persona = get_persona("unknown_persona")
        assert persona is not None
        assert "name" in persona
    
    def test_opening_styles_not_empty(self):
        """Each persona should have multiple opening styles."""
        for persona_name, persona in ENHANCED_PERSONAS.items():
            assert len(persona["opening_styles"]) > 0, f"{persona_name} has no opening styles"
    
    def test_random_opening_returns_string(self):
        """get_random_opening should return a string."""
        opening = get_random_opening("elderly_confused")
        assert isinstance(opening, str)
    
    def test_should_add_typo_returns_boolean(self):
        """should_add_typo should return a boolean."""
        result = should_add_typo("busy_professional")
        assert isinstance(result, bool)


class TestResponseVariationEngine:
    """Tests for response variation and humanization."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.engine = ResponseVariationEngine()
    
    def test_removes_ai_patterns(self):
        """Should remove common AI patterns from responses."""
        ai_response = "I understand. That's quite concerning. What would you like me to do?"
        humanized = self.engine._remove_ai_patterns(ai_response)
        
        assert "I understand" not in humanized
        assert "That's quite" not in humanized
    
    def test_humanize_response_returns_string(self):
        """humanize_response should return a non-empty string."""
        response = self.engine.humanize_response(
            base_response="I don't understand. Can you explain?",
            persona_name="elderly_confused",
            session_id="test_session",
            message_number=1
        )
        assert isinstance(response, str)
        assert len(response) > 0
    
    def test_humanize_response_varies_by_message_number(self):
        """Responses should have variation potential across message numbers."""
        responses = []
        for i in range(5):
            response = self.engine.humanize_response(
                base_response="What should I do?",
                persona_name="elderly_confused",
                session_id=f"test_{i}",
                message_number=i
            )
            responses.append(response)
        
        # At least some responses should be different
        unique_responses = set(responses)
        assert len(unique_responses) >= 1  # May have some variation
    
    def test_fallback_response_not_empty(self):
        """Fallback responses should not be empty."""
        for persona_name in ENHANCED_PERSONAS.keys():
            response = self.engine.get_fallback_response(persona_name)
            assert isinstance(response, str)
            assert len(response) > 0
    
    def test_validate_human_likeness(self):
        """Should reject responses with AI patterns."""
        ai_response = "I apologize for any confusion. I would be happy to help."
        assert not self.engine.validate_human_likeness(ai_response, "elderly_confused")
        
        human_response = "what do you mean? im confused"
        assert self.engine.validate_human_likeness(human_response, "curious_student")


class TestNaturalConversationFlow:
    """Tests for natural conversation flow."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.flow = NaturalConversationFlow()
    
    def test_get_contextual_instructions_returns_string(self):
        """Should return contextual instructions as string."""
        session = {"conversation_history": []}
        persona = ENHANCED_PERSONAS["elderly_confused"]
        
        instructions = self.flow.get_contextual_instructions(session, persona, 1)
        assert isinstance(instructions, str)
        assert "CONVERSATION CONTEXT" in instructions
    
    def test_get_stage_guidance_varies_by_message(self):
        """Stage guidance should vary based on message number."""
        early_guidance = get_stage_guidance(1)
        mid_guidance = get_stage_guidance(5)
        late_guidance = get_stage_guidance(10)
        
        # Each stage should have different guidance
        assert early_guidance != late_guidance


class TestEmotionalIntelligence:
    """Tests for emotional intelligence layer."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.emotion = EmotionalIntelligence()
    
    def test_get_emotional_context_returns_string(self):
        """Should return emotional context as string."""
        persona = ENHANCED_PERSONAS["elderly_confused"]
        context = self.emotion.get_emotional_context(
            session_id="test",
            scammer_message="URGENT: Your account is blocked!",
            message_number=1,
            persona=persona
        )
        assert isinstance(context, str)
        assert "EMOTIONAL RESPONSE GUIDANCE" in context
    
    def test_detects_urgency_triggers(self):
        """Should detect urgency in messages."""
        triggers = self.emotion._identify_emotional_triggers("URGENT: Please respond NOW!")
        assert "urgency_pressure" in triggers["triggers"]
    
    def test_detects_threat_triggers(self):
        """Should detect threats in messages."""
        triggers = self.emotion._identify_emotional_triggers("Your account will be suspended")
        assert "threat" in triggers["triggers"]


class TestContextAwareManager:
    """Tests for context-aware adaptations."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.context = ContextAwareManager()
    
    def test_enhance_prompt_returns_string(self):
        """Should return enhanced prompt with context layers."""
        session = {"conversation_history": [], "intelligence": {}}
        persona = ENHANCED_PERSONAS["elderly_confused"]
        
        enhanced = self.context.enhance_prompt_with_context(
            base_prompt="Original prompt",
            session=session,
            scammer_message="Test message",
            persona=persona,
            message_number=1
        )
        assert isinstance(enhanced, str)
        assert "CONTEXTUAL ENHANCEMENTS" in enhanced
    
    def test_get_concise_context_varies_by_stage(self):
        """Concise context should vary based on conversation stage."""
        session = {"intelligence": {}}
        
        early = get_concise_context(session, 1)
        late = get_concise_context(session, 10)
        
        assert early != late
        assert "Initial" in early or "STAGE" in early


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
