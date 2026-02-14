"""
RAG Configuration for AI Honeypot.
Qdrant vector database setup and collection management.
"""

import os
import logging

logger = logging.getLogger(__name__)

# Qdrant configuration from environment
QDRANT_URL = os.getenv("QDRANT_URL", "")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")

# Global client instance
_qdrant_client = None
_rag_is_functional = False


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

        # Low timeout for initial connection check
        _qdrant_client = QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
            timeout=5
        )
        return _qdrant_client

    except Exception as e:
        logger.error(f"Failed to connect to Qdrant: {e}")
        return None


# Collection configuration
COLLECTIONS = {
    "conversations": {
        "vector_size": 384,
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

# Map string type names to PayloadSchemaType enum values
SCHEMA_TYPE_MAP = {
    "keyword": "KEYWORD",
    "float": "FLOAT",
    "bool": "BOOL",
    "integer": "INTEGER"
}


def initialize_collections() -> bool:
    """
    Create collections and payload indexes if they don't exist.
    Returns True if successful, False otherwise.
    """
    global _rag_is_functional
    client = get_qdrant_client()
    if not client:
        _rag_is_functional = False
        return False

    try:
        from qdrant_client.models import Distance, VectorParams, PayloadSchemaType

        schema_map = {
            "keyword": PayloadSchemaType.KEYWORD,
            "float": PayloadSchemaType.FLOAT,
            "bool": PayloadSchemaType.BOOL,
            "integer": PayloadSchemaType.INTEGER
        }

        # Check connectivity by listing collections
        client.get_collections()
        
        for name, config in COLLECTIONS.items():
            _ensure_collection_exists(client, name, config, Distance, VectorParams)
            _ensure_indexes_exist(client, name, config, schema_map)

        logger.info("✓ RAG system online (Qdrant Cloud)")
        _rag_is_functional = True
        return True

    except Exception as e:
        logger.error(f"RAG initialization failed: {e}")
        _rag_is_functional = False
        return False


def _ensure_collection_exists(client, name, config, Distance, VectorParams):
    """Create collection if it doesn't exist."""
    try:
        client.get_collection(name)
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


def _ensure_indexes_exist(client, name, config, schema_map):
    """Create payload indexes if they don't exist."""
    try:
        collection_info = client.get_collection(name)
        existing_indexes = collection_info.payload_schema

        for field_name, schema_type_str in config.get("indexes", {}).items():
            if field_name in existing_indexes:
                continue

            schema_type = schema_map.get(schema_type_str, schema_map["keyword"])
            try:
                client.create_payload_index(
                    collection_name=name,
                    field_name=field_name,
                    field_schema=schema_type
                )
                logger.info(f"✓ Created {schema_type_str} index for '{name}.{field_name}'")
            except Exception as e:
                logger.warning(f"⚠️ Failed to create index for {name}.{field_name}: {e}")
    except Exception as e:
        logger.warning(f"⚠️ Failed to check indexes for {name}: {e}")


def is_rag_enabled() -> bool:
    """Check if RAG system is configured in environment."""
    return bool(QDRANT_URL and QDRANT_API_KEY)


def is_rag_functional() -> bool:
    """Check if RAG system is properly initialized and reachable."""
    return _rag_is_functional and is_rag_enabled()
