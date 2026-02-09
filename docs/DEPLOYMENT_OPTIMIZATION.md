# Deployment Time Optimization Implementation Guide

This document details the implementation of deployment time optimizations for the AI Honeypot project.

## Overview

Current deployment time is approximately 20+ minutes. These optimizations aim to reduce it to 2-5 minutes.

## Current Bottlenecks

| Bottleneck | Estimated Time | Impact |
|------------|----------------|--------|
| Sentence-transformers model download | 5-10 min | High |
| Model initialization at startup | 3-5 min | High |
| Qdrant connection timeout (30s) | 25-30s | Medium |
| RAG initialization at startup | 2-3 min | Medium |
| Docker build without layer caching | 5-15 min | Medium |

## Implementation Steps

### Step 1: Create Optimized Dockerfile

**File**: `Dockerfile`

```dockerfile
# Use lightweight Python image for faster pulls
FROM python:3.11-slim

WORKDIR /app

# Set Python environment variables for optimal performance
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy requirements first for better layer caching
# This ensures dependency installation is cached unless requirements.txt changes
COPY requirements.txt .

# Install dependencies with no cache dir to reduce image size
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download embedding model during build phase
# This moves the ~3-5 min model download from runtime to build time
# The model is cached by Docker layer caching for subsequent builds
RUN python -c "from fastembed import TextEmbedding; TextEmbedding('sentence-transformers/all-MiniLM-L6-v2')"

# Copy application code
# This layer changes frequently, so it's last to maximize cache reuse
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Rationale**:
- `python:3.11-slim` is ~150MB vs ~900MB for full Python image
- Layer caching: requirements.txt changes less frequently than code
- Pre-download model during build instead of at runtime

---

### Step 2: Switch to FastEmbed

**File**: `app/rag/embeddings.py`

**Current Code**:
```python
from sentence_transformers import SentenceTransformer

def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _model
```

**New Code**:
```python
from fastembed import TextEmbedding

def _get_model():
    """Use fastembed for faster loading."""
    global _model
    if _model is None:
        try:
            # fastembed models are pre-downloaded and cached
            _model = TextEmbedding("sentence-transformers/all-MiniLM-L6-v2")
            logger.info("✓ Loaded fastembed model")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return None
    return _model
```

**Embedding Methods Update**:

```python
class EmbeddingGenerator:
    """Generate embeddings using FastEmbed."""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.dimension = 384  # MiniLM dimension
    
    def embed_text(self, text: str) -> Optional[List[float]]:
        """Embed single text using fastembed."""
        model = _get_model()
        if not model:
            return None
        try:
            # fastembed returns generator, take first result
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
```

**Why FastEmbed**:
- Pre-bundled models, no on-demand downloading
- ~5x faster initialization than sentence-transformers
- Lighter memory footprint
- Already in requirements.txt

---

### Step 3: Reduce Qdrant Timeout

**File**: `app/core/rag_config.py`

**Current Code** (line 34-38):
```python
_qdrant_client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
    timeout=30
)
```

**New Code**:
```python
_qdrant_client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
    timeout=5  # Reduced from 30s for faster failure detection
)
```

**Rationale**:
- Qdrant Cloud connections should establish within 5 seconds
- 30 seconds is excessive for a managed service
- If connection fails, fast failure allows faster retry/logging

---

### Step 4: Lazy RAG Initialization

**File**: `main.py`

**Current Code** (lines 58-66):
```python
# Initialize RAG system if configured
from app.core.rag_config import is_rag_enabled, initialize_collections
if is_rag_enabled():
    if initialize_collections():
        logger.info("✓ RAG system initialized")
    else:
        logger.warning("⚠️ RAG initialization failed, continuing without RAG")
else:
    logger.info("ℹ️ RAG disabled (QDRANT_URL/QDRANT_API_KEY not set)")
```

**New Code - Remove RAG init from lifespan**:
```python
# Remove the RAG initialization block from lifespan
# RAG will be initialized lazily on first request
```

**Add Middleware for Lazy Initialization**:
```python
from fastapi import Request
from app.core.rag_config import is_rag_enabled, initialize_collections

@app.middleware("http")
async def init_rag_on_first_request(request: Request, call_next):
    """Lazy initialize RAG on first request to reduce startup time."""
    if not hasattr(app.state, 'rag_initialized'):
        if is_rag_enabled():
            if initialize_collections():
                logger.info("✓ RAG system initialized on first request")
            else:
                logger.warning("⚠️ RAG initialization failed, continuing without RAG")
        app.state.rag_initialized = True
    return await call_next(request)
```

**Updated Lifespan**:
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    RAG is initialized lazily on first request.
    """
    # Startup
    logger.info("=" * 50)
    logger.info("AI Honeypot API Starting...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug Mode: {settings.DEBUG}")
    logger.info(f"Log Level: {settings.LOG_LEVEL}")
    
    # Validate required settings
    if not settings.GROQ_API_KEY:
        logger.warning("⚠️ GROQ_API_KEY not set! LLM features will fail.")
    else:
        logger.info("✓ GROQ_API_KEY configured")
    
    if not settings.API_SECRET_KEY:
        logger.warning("⚠️ API_SECRET_KEY not set! API authentication disabled.")
    else:
        logger.info("✓ API_SECRET_KEY configured")
    
    logger.info(f"✓ Callback URL: {settings.GUVI_CALLBACK_URL}")
    
    # Note: RAG is initialized lazily on first request
    # This reduces cold start time by 2-3 minutes
    logger.info("=" * 50)
    logger.info("🚀 AI Honeypot API Ready!")
    logger.info("Frontend is in http://localhost:8000/")
    
    yield
    
    # Shutdown
    logger.info("AI Honeypot API Shutting down...")
    logger.info("Goodbye! 👋")
```

**Rationale**:
- RAG initialization can take 2-3 minutes
- Moving to first request eliminates cold start delay
- First API call will be slightly slower, subsequent calls are normal
- Reduces perceived startup time significantly

---

### Step 5: Update Requirements.txt

**File**: `requirements.txt`

**Remove**:
```
sentence-transformers>=2.2.2
```

**Keep**:
```
fastembed>=0.3.0
```

---

## Expected Results Summary

| Optimization | Time Saved | Implementation Complexity |
|-------------|------------|---------------------------|
| Switch to fastembed | 5-10 min | Low |
| Pre-download model in build | 3-5 min | Low |
| Reduce Qdrant timeout | 25-30s | Very Low |
| Lazy RAG initialization | 2-3 min | Low |
| Docker layer caching | 5-15 min | Low |

**Estimated Total Reduction**: 20+ minutes → 2-5 minutes

## Docker Build Optimization Tips

### 1. Multi-stage Build (Optional for Further Optimization)

```dockerfile
# Build stage
FROM python:3.11-slim as builder

WORKDIR /build
COPY requirements.txt .
RUN pip download --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /install /usr/local
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download model
RUN python -c "from fastembed import TextEmbedding; TextEmbedding('sentence-transformers/all-MiniLM-L6-v2')"

COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. BuildKit Caching

```bash
# Enable BuildKit for better caching
export DOCKER_BUILDKIT=1
docker build --progress=plain .
```

### 3. Docker Compose for Development

```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - QDRANT_URL=http://qdrant:6333
      - QDRANT_API_KEY=${QDRANT_API_KEY}
    depends_on:
      - qdrant
    volumes:
      - ./app:/app/app

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
```

## Testing the Optimizations

### 1. Test FastEmbed Integration

```python
from app.rag.embeddings import embedding_generator

# Test single embedding
result = embedding_generator.embed_text("Hello, world!")
print(f"Embedding dimension: {len(result)}")

# Test batch embedding
results = embedding_generator.embed_batch(["Hello", "World"])
print(f"Batch size: {len(results)}")
```

### 2. Test Lazy RAG Initialization

```bash
# Time the first request
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}' \
  --writetimeout 60

# Subsequent requests should be faster
```

### 3. Verify Docker Build Time

```bash
# First build (with model download)
time docker build -t honeypot:opt .

# Subsequent builds (with cache)
time docker build -t honeypot:opt .
```

## Rollback Plan

If issues arise, revert changes by:

1. **Dockerfile**: Delete or revert to previous version
2. **embeddings.py**: Change import back to `sentence_transformers`
3. **rag_config.py**: Restore `timeout=30`
4. **main.py**: Move RAG init back to lifespan
5. **requirements.txt**: Add back `sentence-transformers`

## Monitoring and Validation

After implementation, monitor:

1. **Cold start time**: Time from container start to first request
2. **Model loading time**: Check logs for "Loaded fastembed model"
3. **Qdrant connection**: Verify no timeout errors
4. **Memory usage**: Ensure fastembed uses less memory than sentence-transformers

## Additional Optimization Opportunities

1. **Connection pooling**: Add httpx connection pooling for external APIs
2. **Compiled Python**: Use `pypy` or compile Python modules
3. **Smaller embedding model**: Consider `all-MiniLM-L6-v2` → `paraphrase-MiniLM-L3` for even faster inference
4. **Async initialization**: Load RAG in background during startup
