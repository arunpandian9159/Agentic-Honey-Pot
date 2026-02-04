"""
Embedding generation for RAG system.
Uses sentence-transformers for efficient semantic embeddings.
"""

import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# Lazy-loaded model
_model = None


def _get_model():
    """Lazy load the embedding model."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
            logger.info("✓ Loaded embedding model: all-MiniLM-L6-v2")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            return None
    return _model


class EmbeddingGenerator:
    """Generate embeddings for RAG system."""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize embedding model.
        
        Model choices:
        - all-MiniLM-L6-v2: Fast, 384 dims, good quality (RECOMMENDED)
        - all-mpnet-base-v2: Slower, 768 dims, best quality
        """
        self.model_name = model_name
        self.dimension = 384  # MiniLM dimension
    
    @property
    def model(self):
        """Get the model instance."""
        return _get_model()
    
    def embed_text(self, text: str) -> Optional[List[float]]:
        """Embed single text."""
        if not self.model:
            return None
        try:
            embedding = self.model.encode(text, convert_to_tensor=False)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            return None
    
    def embed_batch(self, texts: List[str]) -> Optional[List[List[float]]]:
        """Embed multiple texts efficiently."""
        if not self.model:
            return None
        try:
            embeddings = self.model.encode(texts, convert_to_tensor=False)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Batch embedding error: {e}")
            return None
    
    def embed_conversation(self, messages: List[Dict]) -> Optional[List[float]]:
        """
        Embed entire conversation.
        Combines scammer + victim messages with context.
        """
        conversation_text = self._format_conversation(messages)
        return self.embed_text(conversation_text)
    
    def _format_conversation(self, messages: List[Dict]) -> str:
        """Format conversation for embedding."""
        formatted = []
        for msg in messages:
            role = "Scammer" if msg.get("sender") == "scammer" else "Victim"
            formatted.append(f"{role}: {msg.get('text', '')}")
        return "\n".join(formatted)


class EmbeddingStrategy:
    """Different embedding strategies for specific use cases."""
    
    @staticmethod
    def for_similar_scams(scammer_message: str, scam_type: str) -> str:
        """Embed to find similar scam scenarios."""
        return f"Scam type: {scam_type}. Message: {scammer_message}"
    
    @staticmethod
    def for_response_examples(
        scammer_message: str,
        persona: str,
        conversation_stage: str
    ) -> str:
        """Embed to find good response examples."""
        return f"Persona: {persona}. Stage: {conversation_stage}. Scammer says: {scammer_message}"
    
    @staticmethod
    def for_extraction_tactics(
        scam_type: str,
        persona: str,
        target_intelligence: str
    ) -> str:
        """Embed to find successful extraction tactics."""
        return f"Extracting {target_intelligence} from {scam_type} as {persona}"
    
    @staticmethod
    def for_persona_consistency(
        persona: str,
        conversation_history: List[Dict]
    ) -> str:
        """Embed to find persona-consistent examples."""
        history_text = " ".join([msg.get("text", "") for msg in conversation_history[-3:]])
        return f"Persona: {persona}. Recent: {history_text}"


# Global instance for convenience
embedding_generator = EmbeddingGenerator()
