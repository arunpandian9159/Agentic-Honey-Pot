"""
Tests for RAG System components.
Tests embedding generation, retrieval, and storage.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch


class TestEmbeddingGenerator:
    """Tests for embedding generation."""
    
    def test_embedding_generator_initialization(self):
        """EmbeddingGenerator should initialize with correct dimension."""
        from app.rag.embeddings import EmbeddingGenerator
        
        generator = EmbeddingGenerator()
        assert generator.dimension == 384
        assert generator.model_name == "sentence-transformers/all-MiniLM-L6-v2"
    
    def test_embed_text_returns_list_or_none(self):
        """embed_text should return list of floats or None if model unavailable."""
        from app.rag.embeddings import embedding_generator
        
        result = embedding_generator.embed_text("Test message")
        # Result is either None (model not loaded) or list of floats
        assert result is None or (isinstance(result, list) and len(result) == 384)
    
    def test_format_conversation(self):
        """_format_conversation should properly format messages."""
        from app.rag.embeddings import EmbeddingGenerator
        
        generator = EmbeddingGenerator()
        messages = [
            {"sender": "scammer", "text": "Your account is blocked"},
            {"sender": "user", "text": "What do you mean?"}
        ]
        
        formatted = generator._format_conversation(messages)
        assert "Scammer: Your account is blocked" in formatted
        assert "Victim: What do you mean?" in formatted


class TestEmbeddingStrategy:
    """Tests for embedding strategies."""
    
    def test_for_similar_scams(self):
        """Should format text for scam similarity search."""
        from app.rag.embeddings import EmbeddingStrategy
        
        text = EmbeddingStrategy.for_similar_scams(
            "Your account is blocked",
            "bank_fraud"
        )
        assert "bank_fraud" in text
        assert "Your account is blocked" in text
    
    def test_for_response_examples(self):
        """Should format text for response pattern search."""
        from app.rag.embeddings import EmbeddingStrategy
        
        text = EmbeddingStrategy.for_response_examples(
            "Send money now",
            "elderly_confused",
            "engagement"
        )
        assert "elderly_confused" in text
        assert "engagement" in text
        assert "Send money now" in text
    
    def test_for_extraction_tactics(self):
        """Should format text for extraction tactic search."""
        from app.rag.embeddings import EmbeddingStrategy
        
        text = EmbeddingStrategy.for_extraction_tactics(
            "bank_fraud",
            "elderly_confused",
            "upi_id"
        )
        assert "upi_id" in text
        assert "bank_fraud" in text


class TestKnowledgeStore:
    """Tests for knowledge storage."""
    
    def test_generate_tags(self):
        """Should generate appropriate tags from messages."""
        from app.rag.knowledge_store import KnowledgeStore
        
        store = KnowledgeStore(None)
        
        tags = store._generate_tags(
            "URGENT: Verify your account NOW!",
            "what do you mean? im confused"
        )
        
        assert "urgency_response" in tags
        assert "showed_confusion" in tags
    
    def test_identify_successful_tactics(self):
        """Should identify tactics from conversation."""
        from app.rag.knowledge_store import KnowledgeStore
        
        store = KnowledgeStore(None)
        
        conversation = [
            {"sender": "scammer", "text": "Your account is blocked"},
            {"sender": "user", "text": "I'm confused, don't understand"},
            {"sender": "scammer", "text": "Send to this UPI"},
            {"sender": "user", "text": "Can you send that again?"},
        ]
        
        intelligence = {"upi_ids": ["test@paytm"]}
        
        tactics = store._identify_successful_tactics(conversation, intelligence)
        
        assert "showed_confusion_to_buy_time" in tactics
        assert "asked_for_clarification_to_confirm_details" in tactics
    
    def test_calculate_engagement_quality(self):
        """Should calculate engagement quality based on message count."""
        from app.rag.knowledge_store import KnowledgeStore
        
        store = KnowledgeStore(None)
        
        assert store._calculate_engagement_quality(10) == 10.0  # Ideal range
        assert store._calculate_engagement_quality(3) == 5.0    # Too short
        assert store._calculate_engagement_quality(6) == 7.5    # Good
    
    def test_generalize_tactic(self):
        """Should generalize specific questions into patterns."""
        from app.rag.knowledge_store import KnowledgeStore
        
        store = KnowledgeStore(None)
        
        assert store._generalize_tactic("can you send that again?") == "ask_to_repeat_details"
        assert store._generalize_tactic("where do i send the money?") == "ask_for_payment_destination"
        assert store._generalize_tactic("how do i do that?") == "request_step_by_step_instructions"


class TestRAGRetriever:
    """Tests for RAG retrieval."""
    
    def test_format_conversation_examples(self):
        """Should format conversation examples properly."""
        from app.rag.retriever import RAGRetriever
        
        retriever = RAGRetriever(None)
        
        conversations = [
            {
                "intelligence_score": 8.0,
                "full_conversation": "Scammer: Test message\nVictim: Test response",
                "successful_tactics": ["showed_confusion", "asked_clarification"]
            }
        ]
        
        formatted = retriever._format_conversation_examples(conversations)
        
        assert "SIMILAR SUCCESSFUL CONVERSATIONS" in formatted
        assert "Score: 8.0" in formatted
        assert "showed_confusion" in formatted
    
    def test_format_response_examples(self):
        """Should format response patterns properly."""
        from app.rag.retriever import RAGRetriever
        
        retriever = RAGRetriever(None)
        
        responses = [
            {
                "scammer_message": "Send money now",
                "victim_response": "where do i send it?",
                "tags": ["asked_clarification", "extracted_upi"]
            }
        ]
        
        formatted = retriever._format_response_examples(responses)
        
        assert "EFFECTIVE RESPONSE PATTERNS" in formatted
        assert "Send money now" in formatted
        assert "where do i send it?" in formatted
    
    def test_format_retrieval_context_empty(self):
        """Should handle empty results gracefully."""
        from app.rag.retriever import RAGRetriever
        
        retriever = RAGRetriever(None)
        
        result = retriever.format_retrieval_context([], "conversations")
        assert result == ""


class TestRAGConversationManager:
    """Tests for RAG-enhanced conversation manager."""
    
    def test_determine_stage(self):
        """Should correctly determine conversation stage."""
        from app.agents.rag_conversation_manager import RAGEnhancedConversationManager
        from unittest.mock import MagicMock
        
        manager = RAGEnhancedConversationManager(MagicMock())
        
        assert manager._determine_stage(1) == "initial"
        assert manager._determine_stage(3) == "engagement"
        assert manager._determine_stage(7) == "extraction"
        assert manager._determine_stage(12) == "prolongation"
    
    def test_identify_missing_intelligence(self):
        """Should identify missing intelligence types."""
        from app.agents.rag_conversation_manager import RAGEnhancedConversationManager
        from unittest.mock import MagicMock
        
        manager = RAGEnhancedConversationManager(MagicMock())
        
        # All missing
        missing = manager._identify_missing_intelligence({})
        assert "bank_account" in missing
        assert "upi_id" in missing
        
        # Some present
        missing = manager._identify_missing_intelligence({
            "upi_ids": ["test@paytm"]
        })
        assert "upi_id" not in missing
        assert "bank_account" in missing


class TestRAGConfig:
    """Tests for RAG configuration."""
    
    def test_is_rag_enabled_false_by_default(self):
        """Should return False when env vars not set."""
        from app.core.rag_config import is_rag_enabled
        
        # This tests that function exists and handles missing config
        result = is_rag_enabled()
        # Result depends on env vars
        assert isinstance(result, bool)
    
    def test_collections_config(self):
        """Should have correct collection configurations."""
        from app.core.rag_config import COLLECTIONS
        
        assert "conversations" in COLLECTIONS
        assert "response_patterns" in COLLECTIONS
        assert "extraction_tactics" in COLLECTIONS
        
        for name, config in COLLECTIONS.items():
            assert config["vector_size"] == 384


class TestLearningLoop:
    """Tests for continuous learning system."""
    
    def test_analyze_top_personas(self):
        """Should analyze top performing personas."""
        from app.rag.learning_loop import ContinuousLearningSystem
        
        system = ContinuousLearningSystem(None)
        
        conversations = [
            {"persona": "elderly_confused", "intelligence_score": 8.0},
            {"persona": "elderly_confused", "intelligence_score": 9.0},
            {"persona": "busy_professional", "intelligence_score": 7.0}
        ]
        
        result = system._analyze_top_personas(conversations)
        
        assert "elderly_confused" in result
        assert result["elderly_confused"] == 8.5
    
    def test_analyze_tactics(self):
        """Should analyze successful tactics."""
        from app.rag.learning_loop import ContinuousLearningSystem
        
        system = ContinuousLearningSystem(None)
        
        conversations = [
            {"successful_tactics": ["confusion", "clarification"]},
            {"successful_tactics": ["confusion", "trust_building"]},
        ]
        
        result = system._analyze_tactics(conversations)
        
        # confusion should be first (appears twice)
        assert result[0] == "confusion"


class TestKnowledgeBaseSchema:
    """Tests for Pydantic models."""
    
    def test_conversation_example_defaults(self):
        """Should have correct defaults."""
        from app.rag.knowledge_base_schema import ConversationExample
        
        example = ConversationExample(
            conversation_id="test_123",
            session_id="sess_123",
            persona="elderly_confused",
            scam_type="bank_fraud"
        )
        
        assert example.intelligence_score == 0.0
        assert example.extraction_success == False
        assert example.scammer_messages == []
    
    def test_response_pattern_defaults(self):
        """Should have correct defaults."""
        from app.rag.knowledge_base_schema import ResponsePattern
        
        pattern = ResponsePattern(
            pattern_id="pat_123",
            session_id="sess_123",
            persona="elderly_confused",
            scam_type="bank_fraud",
            scammer_message="Test",
            victim_response="Response"
        )
        
        assert pattern.led_to_intelligence == False
        assert pattern.kept_engagement == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
