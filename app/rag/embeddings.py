"""
Embedding generation for RAG system.
Uses fastembed for fast, lightweight semantic embeddings.
"""

import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# Lazy-loaded model singleton
_model = None


def _get_model():
    """Get or create the fastembed model singleton."""
    global _model
    if _model is None:
        try:
            from fastembed import TextEmbedding
            _model = TextEmbedding("sentence-transformers/all-MiniLM-L6-v2")
            logger.info("✓ Loaded fastembed model: all-MiniLM-L6-v2")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            return None
    return _model


class EmbeddingGenerator:
    """Generate embeddings using FastEmbed."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.dimension = 384  # MiniLM dimension

    def embed_text(self, text: str) -> Optional[List[float]]:
        """Embed single text."""
        model = _get_model()
        if not model:
            return None
        try:
            embedding = list(model.embed([text]))[0]
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            return None

    def embed_batch(self, texts: List[str]) -> Optional[List[List[float]]]:
        """Embed multiple texts efficiently."""
        model = _get_model()
        if not model:
            return None
        try:
            embeddings = list(model.embed(texts))
            return [e.tolist() for e in embeddings]
        except Exception as e:
            logger.error(f"Batch embedding error: {e}")
            return None

    def embed_conversation(self, messages: List[Dict]) -> Optional[List[float]]:
        """Embed entire conversation by combining all messages."""
        conversation_text = _format_conversation(messages)
        return self.embed_text(conversation_text)


def _format_conversation(messages: List[Dict]) -> str:
    """Format conversation messages for embedding."""
    return "\n".join(
        f"{'Scammer' if msg.get('sender') == 'scammer' else 'Victim'}: {msg.get('text', '')}"
        for msg in messages
    )


class EmbeddingStrategy:
    """Different embedding strategies for specific use cases."""

    @staticmethod
    def for_similar_scams(scammer_message: str, scam_type: str) -> str:
        """Embed to find similar scam scenarios."""
        return f"Scam type: {scam_type}. Message: {scammer_message}"

    @staticmethod
    def for_response_examples(
        scammer_message: str, persona: str, conversation_stage: str
    ) -> str:
        """Embed to find good response examples."""
        return f"Persona: {persona}. Stage: {conversation_stage}. Scammer says: {scammer_message}"

    @staticmethod
    def for_extraction_tactics(
        scam_type: str, persona: str, target_intelligence: str
    ) -> str:
        """Embed to find successful extraction tactics."""
        return f"Extracting {target_intelligence} from {scam_type} as {persona}"

    @staticmethod
    def for_persona_consistency(
        persona: str, conversation_history: List[Dict]
    ) -> str:
        """Embed to find persona-consistent examples."""
        history_text = " ".join(
            msg.get("text", "") for msg in conversation_history[-3:]
        )
        return f"Persona: {persona}. Recent: {history_text}"


# Global instance for convenience
embedding_generator = EmbeddingGenerator()
