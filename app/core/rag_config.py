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
            timeout=5  # Reduced from 30s for faster failure detection
        )
        
        # Diagnostics
        methods = dir(_qdrant_client)
        has_search = "search" in methods
        has_query_points = "query_points" in methods
        logger.info(f"✓ Connected to Qdrant Cloud (search={has_search}, query_points={has_query_points})")
        if not has_search and not has_query_points:
            logger.warning(f"⚠️ Qdrant client missing required retrieval methods! Available: {methods}")
            
        return _qdrant_client
    
    except Exception as e:
        logger.error(f"Failed to connect to Qdrant: {e}")
        return None


# Collection configuration
COLLECTIONS = {
    "conversations": {
        "vector_size": 384,  # MiniLM embedding size
        "description": "Successful conversation examples",
        "indexes": {
            "persona": "keyword",
            "intelligence_score": "float",
            "persona_consistency": "float"
        }
    },
    "response_patterns": {
        "vector_size": 384,
        "description": "High-quality response templates",
        "indexes": {
            "persona": "keyword",
            "led_to_intelligence": "bool"
        }
    },
    "extraction_tactics": {
        "vector_size": 384,
        "description": "Successful intelligence extraction examples",
        "indexes": {
            "intelligence_type": "keyword",
            "success_rate": "float"
        }
    }
}


def initialize_collections() -> bool:
    """
    Create collections and payload indexes if they don't exist.
    Returns True if successful, False otherwise.
    """
    client = get_qdrant_client()
    if not client:
        return False
    
    try:
        from qdrant_client.models import Distance, VectorParams, PayloadSchemaType
        
        for name, config in COLLECTIONS.items():
            # 1. Ensure collection exists
            try:
                collection_info = client.get_collection(name)
                logger.debug(f"✓ Collection '{name}' exists")
            except Exception:
                client.create_collection(
                    collection_name=name,
                    vectors_config=VectorParams(
                        size=config["vector_size"],
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"✓ Created collection '{name}'")
                collection_info = client.get_collection(name)

            # 2. Ensure payload indexes exist for filtered fields
            existing_indexes = collection_info.payload_schema
            for field_name, schema_type_str in config.get("indexes", {}).items():
                if field_name not in existing_indexes:
                    # Map string type to PayloadSchemaType enum
                    schema_map = {
                        "keyword": PayloadSchemaType.KEYWORD,
                        "float": PayloadSchemaType.FLOAT,
                        "bool": PayloadSchemaType.BOOL,
                        "integer": PayloadSchemaType.INTEGER
                    }
                    schema_type = schema_map.get(schema_type_str, PayloadSchemaType.KEYWORD)
                    
                    try:
                        client.create_payload_index(
                            collection_name=name,
                            field_name=field_name,
                            field_schema=schema_type
                        )
                        logger.info(f"✓ Created {schema_type_str} index for '{name}.{field_name}'")
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to create index for {name}.{field_name}: {e}")
        
        return True
    
    except Exception as e:
        logger.error(f"Failed to initialize collections: {e}")
        return False


def is_rag_enabled() -> bool:
    """Check if RAG system is properly configured."""
    return bool(QDRANT_URL and QDRANT_API_KEY)
