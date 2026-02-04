"""
RAG Configuration for AI Honeypot.
Qdrant vector database setup and collection management.
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Qdrant configuration from environment
QDRANT_URL = os.getenv("QDRANT_URL", "")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")

# Global client instance
_qdrant_client = None


def get_qdrant_client():
    """Get or create Qdrant client singleton."""
    global _qdrant_client
    
    if _qdrant_client is not None:
        return _qdrant_client
    
    if not QDRANT_URL or not QDRANT_API_KEY:
        logger.warning("⚠️ QDRANT_URL or QDRANT_API_KEY not set. RAG disabled.")
        return None
    
    try:
        from qdrant_client import QdrantClient
        
        _qdrant_client = QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
            timeout=30
        )
        logger.info("✓ Connected to Qdrant Cloud")
        return _qdrant_client
    
    except Exception as e:
        logger.error(f"Failed to connect to Qdrant: {e}")
        return None


# Collection configuration
COLLECTIONS = {
    "conversations": {
        "vector_size": 384,  # MiniLM embedding size
        "description": "Successful conversation examples"
    },
    "response_patterns": {
        "vector_size": 384,
        "description": "High-quality response templates"
    },
    "extraction_tactics": {
        "vector_size": 384,
        "description": "Successful intelligence extraction examples"
    }
}


def initialize_collections() -> bool:
    """
    Create collections if they don't exist.
    Returns True if successful, False otherwise.
    """
    client = get_qdrant_client()
    if not client:
        return False
    
    try:
        from qdrant_client.models import Distance, VectorParams
        
        for name, config in COLLECTIONS.items():
            try:
                client.get_collection(name)
                logger.info(f"✓ Collection '{name}' exists")
            except Exception:
                client.create_collection(
                    collection_name=name,
                    vectors_config=VectorParams(
                        size=config["vector_size"],
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"✓ Created collection '{name}'")
        
        return True
    
    except Exception as e:
        logger.error(f"Failed to initialize collections: {e}")
        return False


def is_rag_enabled() -> bool:
    """Check if RAG system is properly configured."""
    return bool(QDRANT_URL and QDRANT_API_KEY)
