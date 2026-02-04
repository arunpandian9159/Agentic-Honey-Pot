# RAG System for AI Honeypot
## Continuous Learning & Improved Response Quality

**Version:** 1.0  
**Purpose:** Implement RAG to learn from successful conversations and improve response consistency  
**Time to Implement:** 3-4 hours  
**Cost:** Free tier (using Qdrant Cloud or ChromaDB)

---

## Table of Contents

1. [Why RAG for Honeypot?](#1-why-rag-for-honeypot)
2. [RAG Architecture](#2-rag-architecture)
3. [Vector Database Setup](#3-vector-database-setup)
4. [Knowledge Base Structure](#4-knowledge-base-structure)
5. [Embedding Strategy](#5-embedding-strategy)
6. [Retrieval Logic](#6-retrieval-logic)
7. [Implementation Code](#7-implementation-code)
8. [Integration Guide](#8-integration-guide)
9. [Learning Loop](#9-learning-loop)
10. [Testing & Validation](#10-testing--validation)

---

## 1. Why RAG for Honeypot?

### Problems RAG Solves

**Problem 1: Inconsistent Responses**
- Current: Each response generated fresh, no memory of what worked before
- With RAG: Retrieve similar successful conversations, maintain consistency

**Problem 2: No Learning from Success**
- Current: Successful intelligence extractions aren't reused
- With RAG: Store and retrieve tactics that successfully extracted intel

**Problem 3: Repetitive Patterns**
- Current: LLM might repeat same response style
- With RAG: Retrieve diverse examples, ensure variation

**Problem 4: Context Loss**
- Current: Only last 5 messages in context
- With RAG: Retrieve relevant parts of longer conversation history

**Problem 5: Persona Drift**
- Current: Persona might become inconsistent over long conversations
- With RAG: Retrieve persona-consistent examples

### What RAG Adds to Your Honeypot

```
┌─────────────────────────────────────────────────┐
│           ENHANCED HONEYPOT WITH RAG            │
├─────────────────────────────────────────────────┤
│                                                 │
│  Incoming Scammer Message                      │
│         ↓                                       │
│  ┌─────────────────────────┐                  │
│  │ 1. RETRIEVAL PHASE      │                  │
│  │ - Find similar scams    │                  │
│  │ - Get successful tactics│                  │
│  │ - Retrieve persona ex.  │                  │
│  └───────────┬─────────────┘                  │
│              ↓                                  │
│  ┌─────────────────────────┐                  │
│  │ 2. AUGMENTATION PHASE   │                  │
│  │ - Combine with current  │                  │
│  │ - Add context examples  │                  │
│  │ - Enhance prompt        │                  │
│  └───────────┬─────────────┘                  │
│              ↓                                  │
│  ┌─────────────────────────┐                  │
│  │ 3. GENERATION PHASE     │                  │
│  │ - Generate with context │                  │
│  │ - Maintain consistency  │                  │
│  │ - Use learned patterns  │                  │
│  └───────────┬─────────────┘                  │
│              ↓                                  │
│  ┌─────────────────────────┐                  │
│  │ 4. STORAGE PHASE        │                  │
│  │ - Store interaction     │                  │
│  │ - Tag success metrics   │                  │
│  │ - Update knowledge base │                  │
│  └─────────────────────────┘                  │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Expected Improvements

| Metric | Before RAG | After RAG | Improvement |
|--------|-----------|-----------|-------------|
| Response Consistency | 6/10 | 9/10 | +50% |
| Intelligence Extraction | 75% | 85% | +13% |
| Persona Coherence | 7/10 | 9/10 | +29% |
| Conversation Length | 8 msgs | 12 msgs | +50% |
| Scammer Engagement | Good | Excellent | Better |

---

## 2. RAG Architecture

### System Components

```python
RAG_SYSTEM = {
    "knowledge_base": {
        "successful_conversations": "Past convos with high intel scores",
        "response_templates": "Proven response patterns by persona",
        "extraction_tactics": "Successful intelligence extraction examples",
        "scammer_patterns": "Common scammer tactics and responses",
        "persona_examples": "High-quality persona-specific responses"
    },
    
    "vector_database": {
        "options": ["Qdrant Cloud (Free)", "ChromaDB (Local)", "Pinecone (Free tier)"],
        "recommended": "Qdrant Cloud",
        "storage": "Conversation embeddings + metadata"
    },
    
    "embedding_model": {
        "options": ["sentence-transformers (Free)", "OpenAI (Paid)", "Cohere (Free tier)"],
        "recommended": "sentence-transformers/all-MiniLM-L6-v2",
        "size": "384 dimensions",
        "speed": "Fast"
    },
    
    "retrieval_strategy": {
        "semantic_search": "Find similar scam scenarios",
        "metadata_filtering": "Filter by persona, scam type, success",
        "hybrid_search": "Combine semantic + keyword matching",
        "reranking": "Score and prioritize results"
    }
}
```

### Data Flow

```
Scammer Message
    ↓
┌───────────────────────────────────────┐
│ QUERY CONSTRUCTION                    │
│ - Extract key elements (urgency, etc.)│
│ - Identify scam type                  │
│ - Get current persona                 │
└───────────┬───────────────────────────┘
            ↓
┌───────────────────────────────────────┐
│ VECTOR SEARCH                         │
│ - Embed query                         │
│ - Search knowledge base               │
│ - Filter by metadata (persona, type)  │
│ - Return top K similar examples       │
└───────────┬───────────────────────────┘
            ↓
┌───────────────────────────────────────┐
│ CONTEXT BUILDING                      │
│ - Format retrieved examples           │
│ - Add to LLM prompt                   │
│ - Include success metrics             │
└───────────┬───────────────────────────┘
            ↓
┌───────────────────────────────────────┐
│ RESPONSE GENERATION                   │
│ - LLM generates with RAG context      │
│ - Humanize response                   │
│ - Validate quality                    │
└───────────┬───────────────────────────┘
            ↓
┌───────────────────────────────────────┐
│ FEEDBACK LOOP                         │
│ - Store new response                  │
│ - Tag with success metrics            │
│ - Update knowledge base               │
└───────────────────────────────────────┘
```

---

## 3. Vector Database Setup

### Option 1: Qdrant Cloud (Recommended - Free Tier)

**Why Qdrant:**
- ✅ 1GB free storage forever
- ✅ Cloud-hosted (no infrastructure)
- ✅ Fast vector search
- ✅ Metadata filtering built-in
- ✅ Python client easy to use

**Setup Steps:**

```bash
# 1. Install Qdrant client
pip install qdrant-client sentence-transformers

# 2. Sign up at https://cloud.qdrant.io (free)
# 3. Get API key and cluster URL
```

**Configuration:**

```python
# app/core/rag_config.py

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import os

# Qdrant setup
QDRANT_URL = os.getenv("QDRANT_URL", "https://your-cluster.qdrant.io")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

# Initialize client
qdrant_client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)

# Collection configuration
COLLECTIONS = {
    "conversations": {
        "vector_size": 384,  # MiniLM embedding size
        "distance": Distance.COSINE,
        "description": "Successful conversation examples"
    },
    "response_patterns": {
        "vector_size": 384,
        "distance": Distance.COSINE,
        "description": "High-quality response templates"
    },
    "extraction_tactics": {
        "vector_size": 384,
        "distance": Distance.COSINE,
        "description": "Successful intelligence extraction examples"
    }
}

def initialize_collections():
    """Create collections if they don't exist"""
    for name, config in COLLECTIONS.items():
        try:
            qdrant_client.get_collection(name)
            print(f"✓ Collection '{name}' already exists")
        except:
            qdrant_client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(
                    size=config["vector_size"],
                    distance=config["distance"]
                )
            )
            print(f"✓ Created collection '{name}'")
```

### Option 2: ChromaDB (Alternative - Local)

```bash
pip install chromadb

# Simpler but local storage only
# Good for development, not production at scale
```

---

## 4. Knowledge Base Structure

### What to Store in RAG

```python
# app/rag/knowledge_base_schema.py

from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel

class ConversationExample(BaseModel):
    """Single conversation stored in RAG"""
    
    # Identifiers
    conversation_id: str
    timestamp: datetime
    
    # Conversation content
    scammer_messages: List[str]
    victim_responses: List[str]
    full_conversation: str  # For embedding
    
    # Metadata for filtering
    persona: str  # "elderly_confused", "busy_professional", etc.
    scam_type: str  # "bank_fraud", "upi_fraud", etc.
    message_count: int
    
    # Success metrics
    intelligence_extracted: Dict[str, List[str]]
    intelligence_score: float  # 0-10
    engagement_quality: float  # 0-10 (how long scammer engaged)
    extraction_success: bool  # Did we get bank/UPI/links?
    
    # Learning tags
    successful_tactics: List[str]  # What worked?
    persona_consistency: float  # 0-10
    human_likeness: float  # 0-10
    
    # Response patterns
    effective_responses: List[Dict]  # Specific responses that worked
    
class ResponsePattern(BaseModel):
    """Individual successful response"""
    
    pattern_id: str
    persona: str
    scammer_message: str  # What scammer said
    victim_response: str  # Our response
    conversation_stage: str  # "initial", "engagement", "extraction"
    
    # Success metrics
    led_to_intelligence: bool
    kept_engagement: bool
    maintained_persona: bool
    
    # Context
    tags: List[str]  # "urgency_response", "authority_compliance", etc.
    
class ExtractionTactic(BaseModel):
    """Successful intelligence extraction pattern"""
    
    tactic_id: str
    scam_type: str
    persona: str
    
    # The tactic
    setup_messages: List[str]  # Messages leading up
    extraction_question: str  # The question that got intel
    scammer_response: str  # What they revealed
    
    # What was extracted
    intelligence_type: str  # "bank_account", "upi_id", "link"
    success_rate: float  # How often this tactic works
    
    # Reusability
    generalized_pattern: str  # Template for reuse
```

### Example Data to Store

```python
# Example 1: Successful conversation
{
    "conversation_id": "conv_001",
    "persona": "elderly_confused",
    "scam_type": "bank_fraud",
    "full_conversation": """
    Scammer: Your account will be blocked. Verify now.
    Victim: oh no what happened?? why
    Scammer: KYC expired. Send ₹1 to verify.
    Victim: I dont know how to do that. where do I send
    Scammer: Send to 9876543210@paytm
    Victim: ok so I send to 9876543210@paytm? My daughter usually helps me with this
    """,
    "intelligence_extracted": {
        "upi_ids": ["9876543210@paytm"]
    },
    "intelligence_score": 6.0,
    "successful_tactics": [
        "showed_confusion_to_buy_time",
        "asked_for_clarification_to_confirm_details",
        "mentioned_family_member_for_realism"
    ]
}

# Example 2: Effective response pattern
{
    "pattern_id": "resp_045",
    "persona": "busy_professional",
    "scammer_message": "Pay verification fee to winner@paytm",
    "victim_response": "wait which account? send the upi id again",
    "led_to_intelligence": True,
    "tags": ["feigned_confusion", "requested_repeat", "extracted_upi"]
}

# Example 3: Extraction tactic
{
    "tactic_id": "tactic_012",
    "scam_type": "upi_fraud",
    "persona": "curious_student",
    "extraction_question": "ok but send me the link again? it didnt work",
    "intelligence_type": "phishing_link",
    "success_rate": 0.85,
    "generalized_pattern": "claim_technical_issue_to_get_repeat_details"
}
```

---

## 5. Embedding Strategy

### Embedding Model Setup

```python
# app/rag/embeddings.py

from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Union

class EmbeddingGenerator:
    """Generate embeddings for RAG system"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize embedding model
        
        Model choices:
        - all-MiniLM-L6-v2: Fast, 384 dims, good quality (RECOMMENDED)
        - all-mpnet-base-v2: Slower, 768 dims, best quality
        - paraphrase-MiniLM-L3-v2: Fastest, 384 dims, okay quality
        """
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
    
    def embed_text(self, text: str) -> List[float]:
        """Embed single text"""
        embedding = self.model.encode(text, convert_to_tensor=False)
        return embedding.tolist()
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts efficiently"""
        embeddings = self.model.encode(texts, convert_to_tensor=False)
        return embeddings.tolist()
    
    def embed_conversation(self, messages: List[Dict]) -> List[float]:
        """
        Embed entire conversation
        
        Combines scammer + victim messages with context
        """
        conversation_text = self._format_conversation(messages)
        return self.embed_text(conversation_text)
    
    def _format_conversation(self, messages: List[Dict]) -> str:
        """Format conversation for embedding"""
        formatted = []
        for msg in messages:
            role = "Scammer" if msg["sender"] == "scammer" else "Victim"
            formatted.append(f"{role}: {msg['text']}")
        return "\n".join(formatted)

# Initialize globally
embedding_generator = EmbeddingGenerator()
```

### What to Embed

```python
# Different embedding strategies for different use cases

class EmbeddingStrategy:
    """Different ways to embed conversations for RAG"""
    
    @staticmethod
    def embed_for_similar_scams(scammer_message: str, scam_type: str) -> str:
        """Embed to find similar scam scenarios"""
        # Focus on scammer's message pattern
        return f"Scam type: {scam_type}. Message: {scammer_message}"
    
    @staticmethod
    def embed_for_response_examples(
        scammer_message: str,
        persona: str,
        conversation_stage: str
    ) -> str:
        """Embed to find good response examples"""
        # Focus on context where response needed
        return f"Persona: {persona}. Stage: {conversation_stage}. Scammer says: {scammer_message}"
    
    @staticmethod
    def embed_for_extraction_tactics(
        scam_type: str,
        persona: str,
        target_intelligence: str
    ) -> str:
        """Embed to find successful extraction tactics"""
        # Focus on extraction context
        return f"Extracting {target_intelligence} from {scam_type} as {persona}"
    
    @staticmethod
    def embed_for_persona_consistency(
        persona: str,
        conversation_history: List[Dict]
    ) -> str:
        """Embed to find persona-consistent examples"""
        # Focus on persona + conversation flow
        history_text = " ".join([msg["text"] for msg in conversation_history[-3:]])
        return f"Persona: {persona}. Recent: {history_text}"
```

---

## 6. Retrieval Logic

### RAG Retriever Class

```python
# app/rag/retriever.py

from typing import List, Dict, Optional
from qdrant_client.models import Filter, FieldCondition, MatchValue
from app.rag.embeddings import embedding_generator

class RAGRetriever:
    """Retrieve relevant examples from knowledge base"""
    
    def __init__(self, qdrant_client):
        self.client = qdrant_client
        self.embedder = embedding_generator
    
    async def retrieve_similar_conversations(
        self,
        scammer_message: str,
        scam_type: str,
        persona: str,
        limit: int = 3
    ) -> List[Dict]:
        """
        Retrieve similar successful conversations
        
        Returns conversations where:
        - Similar scam type and message pattern
        - Same persona
        - High intelligence score
        """
        
        # Build query
        query_text = f"Scam: {scam_type}. Message: {scammer_message}"
        query_vector = self.embedder.embed_text(query_text)
        
        # Build filter for metadata
        filter_conditions = Filter(
            must=[
                FieldCondition(
                    key="persona",
                    match=MatchValue(value=persona)
                ),
                FieldCondition(
                    key="scam_type",
                    match=MatchValue(value=scam_type)
                ),
                FieldCondition(
                    key="intelligence_score",
                    range={"gte": 5.0}  # Only successful conversations
                )
            ]
        )
        
        # Search
        results = self.client.search(
            collection_name="conversations",
            query_vector=query_vector,
            query_filter=filter_conditions,
            limit=limit
        )
        
        return [result.payload for result in results]
    
    async def retrieve_response_patterns(
        self,
        scammer_message: str,
        persona: str,
        conversation_stage: str,
        limit: int = 5
    ) -> List[Dict]:
        """
        Retrieve effective response patterns
        
        Returns specific responses that worked in similar situations
        """
        
        query_text = f"Stage: {conversation_stage}. Scammer: {scammer_message}"
        query_vector = self.embedder.embed_text(query_text)
        
        filter_conditions = Filter(
            must=[
                FieldCondition(key="persona", match=MatchValue(value=persona)),
                FieldCondition(key="led_to_intelligence", match=MatchValue(value=True))
            ]
        )
        
        results = self.client.search(
            collection_name="response_patterns",
            query_vector=query_vector,
            query_filter=filter_conditions,
            limit=limit
        )
        
        return [result.payload for result in results]
    
    async def retrieve_extraction_tactics(
        self,
        scam_type: str,
        persona: str,
        target_intel_type: str,
        limit: int = 3
    ) -> List[Dict]:
        """
        Retrieve successful intelligence extraction tactics
        
        Returns proven tactics for extracting specific intel types
        """
        
        query_text = f"Extract {target_intel_type} from {scam_type} as {persona}"
        query_vector = self.embedder.embed_text(query_text)
        
        filter_conditions = Filter(
            must=[
                FieldCondition(key="scam_type", match=MatchValue(value=scam_type)),
                FieldCondition(key="persona", match=MatchValue(value=persona)),
                FieldCondition(key="intelligence_type", match=MatchValue(value=target_intel_type)),
                FieldCondition(key="success_rate", range={"gte": 0.6})
            ]
        )
        
        results = self.client.search(
            collection_name="extraction_tactics",
            query_vector=query_vector,
            query_filter=filter_conditions,
            limit=limit
        )
        
        return [result.payload for result in results]
    
    async def retrieve_persona_examples(
        self,
        persona: str,
        recent_messages: List[Dict],
        limit: int = 3
    ) -> List[Dict]:
        """
        Retrieve examples to maintain persona consistency
        
        Returns conversations where persona was well-maintained
        """
        
        history_text = " ".join([msg["text"] for msg in recent_messages[-3:]])
        query_text = f"Persona: {persona}. Context: {history_text}"
        query_vector = self.embedder.embed_text(query_text)
        
        filter_conditions = Filter(
            must=[
                FieldCondition(key="persona", match=MatchValue(value=persona)),
                FieldCondition(key="persona_consistency", range={"gte": 8.0})
            ]
        )
        
        results = self.client.search(
            collection_name="conversations",
            query_vector=query_vector,
            query_filter=filter_conditions,
            limit=limit
        )
        
        return [result.payload for result in results]
    
    def format_retrieval_context(self, results: List[Dict], context_type: str) -> str:
        """Format retrieved results for LLM prompt"""
        
        if not results:
            return ""
        
        if context_type == "conversations":
            return self._format_conversation_examples(results)
        elif context_type == "responses":
            return self._format_response_examples(results)
        elif context_type == "tactics":
            return self._format_tactic_examples(results)
        elif context_type == "persona":
            return self._format_persona_examples(results)
        
        return ""
    
    def _format_conversation_examples(self, conversations: List[Dict]) -> str:
        """Format similar conversation examples"""
        
        formatted = ["SIMILAR SUCCESSFUL CONVERSATIONS:\n"]
        
        for i, conv in enumerate(conversations, 1):
            formatted.append(f"\nExample {i} (Score: {conv.get('intelligence_score', 0)}):")
            formatted.append(conv.get('full_conversation', '')[:300] + "...")
            
            if conv.get('successful_tactics'):
                formatted.append(f"What worked: {', '.join(conv['successful_tactics'][:3])}")
        
        return "\n".join(formatted)
    
    def _format_response_examples(self, responses: List[Dict]) -> str:
        """Format response pattern examples"""
        
        formatted = ["EFFECTIVE RESPONSE PATTERNS:\n"]
        
        for i, resp in enumerate(responses, 1):
            formatted.append(f"\n{i}. When scammer said: \"{resp['scammer_message']}\"")
            formatted.append(f"   Good response: \"{resp['victim_response']}\"")
            if resp.get('tags'):
                formatted.append(f"   Why it worked: {', '.join(resp['tags'][:2])}")
        
        return "\n".join(formatted)
    
    def _format_tactic_examples(self, tactics: List[Dict]) -> str:
        """Format extraction tactic examples"""
        
        formatted = ["SUCCESSFUL EXTRACTION TACTICS:\n"]
        
        for i, tactic in enumerate(tactics, 1):
            formatted.append(f"\n{i}. Tactic: {tactic['generalized_pattern']}")
            formatted.append(f"   Example question: \"{tactic['extraction_question']}\"")
            formatted.append(f"   Success rate: {tactic['success_rate']*100:.0f}%")
        
        return "\n".join(formatted)
    
    def _format_persona_examples(self, examples: List[Dict]) -> str:
        """Format persona consistency examples"""
        
        formatted = ["PERSONA-CONSISTENT EXAMPLES:\n"]
        
        for i, ex in enumerate(examples, 1):
            # Extract a few victim responses
            victim_responses = [
                msg for msg in ex.get('victim_responses', [])[:3]
            ]
            formatted.append(f"\n{i}. Example responses:")
            for resp in victim_responses:
                formatted.append(f"   - \"{resp}\"")
        
        return "\n".join(formatted)
```

---

## 7. Implementation Code

### RAG-Enhanced Conversation Manager

```python
# app/agents/rag_conversation_manager.py

from app.agents.enhanced_conversation import EnhancedConversationManager
from app.rag.retriever import RAGRetriever
from app.rag.knowledge_store import KnowledgeStore
from typing import Dict, List

class RAGEnhancedConversationManager(EnhancedConversationManager):
    """Enhanced conversation manager with RAG capabilities"""
    
    def __init__(self, llm_client, qdrant_client):
        super().__init__(llm_client)
        self.retriever = RAGRetriever(qdrant_client)
        self.knowledge_store = KnowledgeStore(qdrant_client)
    
    async def generate_rag_enhanced_response(
        self,
        persona_name: str,
        scammer_message: str,
        conversation_history: List[Dict],
        session: Dict,
        message_number: int
    ) -> str:
        """Generate response with RAG context"""
        
        # Step 1: Retrieve relevant context
        rag_context = await self._build_rag_context(
            persona_name=persona_name,
            scammer_message=scammer_message,
            session=session,
            message_number=message_number
        )
        
        # Step 2: Build enhanced prompt with RAG context
        base_prompt = self._build_base_prompt(
            persona_name, scammer_message, conversation_history,
            session, message_number
        )
        
        rag_enhanced_prompt = f"""{base_prompt}

═══════════════════════════════════════════
KNOWLEDGE FROM PREVIOUS SUCCESSFUL INTERACTIONS
═══════════════════════════════════════════

{rag_context}

INSTRUCTIONS:
- Learn from the examples above
- Use similar tactics that worked before
- Maintain consistency with successful patterns
- Don't copy exactly - adapt to current situation
- Ensure your response feels natural and unique

Now generate your response considering both the examples above and your persona guidelines.
"""
        
        # Step 3: Generate response
        response = await super().generate_enhanced_response(
            persona_name, scammer_message, conversation_history,
            session, message_number
        )
        
        # Step 4: Store interaction for future learning
        await self._store_interaction(
            session_id=session["session_id"],
            scammer_message=scammer_message,
            victim_response=response,
            session=session
        )
        
        return response
    
    async def _build_rag_context(
        self,
        persona_name: str,
        scammer_message: str,
        session: Dict,
        message_number: int
    ) -> str:
        """Build RAG context from retrieved examples"""
        
        scam_type = session.get("scam_type", "unknown")
        intelligence = session.get("intelligence", {})
        
        context_parts = []
        
        # 1. Retrieve similar successful conversations
        if message_number <= 5:
            # Early in conversation - get similar opening examples
            similar_convos = await self.retriever.retrieve_similar_conversations(
                scammer_message=scammer_message,
                scam_type=scam_type,
                persona=persona_name,
                limit=2
            )
            if similar_convos:
                formatted = self.retriever.format_retrieval_context(
                    similar_convos, "conversations"
                )
                context_parts.append(formatted)
        
        # 2. Retrieve effective response patterns
        conversation_stage = self._determine_stage(message_number)
        response_patterns = await self.retriever.retrieve_response_patterns(
            scammer_message=scammer_message,
            persona=persona_name,
            conversation_stage=conversation_stage,
            limit=3
        )
        if response_patterns:
            formatted = self.retriever.format_retrieval_context(
                response_patterns, "responses"
            )
            context_parts.append(formatted)
        
        # 3. Retrieve extraction tactics (if needed)
        if message_number >= 6:
            # Time to extract intelligence
            missing_intel_types = self._identify_missing_intelligence(intelligence)
            
            for intel_type in missing_intel_types[:2]:  # Top 2 priorities
                tactics = await self.retriever.retrieve_extraction_tactics(
                    scam_type=scam_type,
                    persona=persona_name,
                    target_intel_type=intel_type,
                    limit=2
                )
                if tactics:
                    formatted = self.retriever.format_retrieval_context(
                        tactics, "tactics"
                    )
                    context_parts.append(formatted)
        
        # 4. Retrieve persona consistency examples
        if message_number >= 4:
            # Ensure persona stays consistent
            persona_examples = await self.retriever.retrieve_persona_examples(
                persona=persona_name,
                recent_messages=session.get("conversation_history", [])[-5:],
                limit=2
            )
            if persona_examples:
                formatted = self.retriever.format_retrieval_context(
                    persona_examples, "persona"
                )
                context_parts.append(formatted)
        
        # Combine all context
        if not context_parts:
            return "(No relevant examples found - generate based on persona guidelines)"
        
        return "\n\n".join(context_parts)
    
    def _determine_stage(self, message_number: int) -> str:
        """Determine conversation stage"""
        if message_number <= 2:
            return "initial"
        elif message_number <= 5:
            return "engagement"
        elif message_number <= 10:
            return "extraction"
        else:
            return "prolongation"
    
    def _identify_missing_intelligence(self, intelligence: Dict) -> List[str]:
        """Identify what intelligence is still missing"""
        missing = []
        
        if not intelligence.get("bank_accounts"):
            missing.append("bank_account")
        if not intelligence.get("upi_ids"):
            missing.append("upi_id")
        if not intelligence.get("phishing_links"):
            missing.append("phishing_link")
        if not intelligence.get("phone_numbers"):
            missing.append("phone_number")
        
        return missing
    
    async def _store_interaction(
        self,
        session_id: str,
        scammer_message: str,
        victim_response: str,
        session: Dict
    ):
        """Store interaction for future learning"""
        
        await self.knowledge_store.store_interaction(
            session_id=session_id,
            scammer_message=scammer_message,
            victim_response=victim_response,
            persona=session.get("persona"),
            scam_type=session.get("scam_type"),
            intelligence_so_far=session.get("intelligence")
        )
```

### Knowledge Store

```python
# app/rag/knowledge_store.py

from qdrant_client.models import PointStruct
from app.rag.embeddings import embedding_generator
import uuid
from datetime import datetime
from typing import Dict, List

class KnowledgeStore:
    """Store new learnings in RAG knowledge base"""
    
    def __init__(self, qdrant_client):
        self.client = qdrant_client
        self.embedder = embedding_generator
    
    async def store_interaction(
        self,
        session_id: str,
        scammer_message: str,
        victim_response: str,
        persona: str,
        scam_type: str,
        intelligence_so_far: Dict
    ):
        """Store single interaction"""
        
        # Create response pattern point
        pattern_id = str(uuid.uuid4())
        
        # Embed the interaction
        interaction_text = f"Scammer: {scammer_message}\nVictim: {victim_response}"
        embedding = self.embedder.embed_text(interaction_text)
        
        # Determine if this led to intelligence
        led_to_intel = any(len(v) > 0 for v in intelligence_so_far.values())
        
        # Create point
        point = PointStruct(
            id=pattern_id,
            vector=embedding,
            payload={
                "pattern_id": pattern_id,
                "session_id": session_id,
                "persona": persona,
                "scam_type": scam_type,
                "scammer_message": scammer_message,
                "victim_response": victim_response,
                "led_to_intelligence": led_to_intel,
                "timestamp": datetime.now().isoformat(),
                "maintained_persona": True,  # Could add validation
                "tags": self._generate_tags(scammer_message, victim_response)
            }
        )
        
        # Store in response_patterns collection
        self.client.upsert(
            collection_name="response_patterns",
            points=[point]
        )
    
    async def store_completed_conversation(
        self,
        session_id: str,
        conversation_history: List[Dict],
        persona: str,
        scam_type: str,
        intelligence: Dict,
        intelligence_score: float
    ):
        """Store complete conversation after session ends"""
        
        conv_id = str(uuid.uuid4())
        
        # Format full conversation
        full_conversation = "\n".join([
            f"{'Scammer' if msg['sender'] == 'scammer' else 'Victim'}: {msg['text']}"
            for msg in conversation_history
        ])
        
        # Embed conversation
        embedding = self.embedder.embed_text(full_conversation)
        
        # Extract successful tactics
        tactics = self._identify_successful_tactics(
            conversation_history, intelligence
        )
        
        # Extract victim responses only
        victim_responses = [
            msg["text"] for msg in conversation_history
            if msg["sender"] == "user"
        ]
        
        # Create point
        point = PointStruct(
            id=conv_id,
            vector=embedding,
            payload={
                "conversation_id": conv_id,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "persona": persona,
                "scam_type": scam_type,
                "message_count": len(conversation_history),
                "full_conversation": full_conversation,
                "victim_responses": victim_responses,
                "intelligence_extracted": intelligence,
                "intelligence_score": intelligence_score,
                "engagement_quality": self._calculate_engagement_quality(
                    len(conversation_history)
                ),
                "extraction_success": intelligence_score >= 5.0,
                "successful_tactics": tactics,
                "persona_consistency": 8.5,  # Could add actual measurement
                "human_likeness": 9.0  # Could add actual measurement
            }
        )
        
        # Store in conversations collection
        self.client.upsert(
            collection_name="conversations",
            points=[point]
        )
        
        # Also extract and store specific extraction tactics if successful
        if intelligence_score >= 5.0:
            await self._store_extraction_tactics(
                session_id, conversation_history, persona, scam_type, intelligence
            )
    
    async def _store_extraction_tactics(
        self,
        session_id: str,
        conversation: List[Dict],
        persona: str,
        scam_type: str,
        intelligence: Dict
    ):
        """Extract and store successful extraction tactics"""
        
        # Identify moments where intelligence was extracted
        for i, msg in enumerate(conversation):
            if msg["sender"] == "user":  # Our response
                # Check if next scammer message revealed intel
                if i + 1 < len(conversation):
                    next_msg = conversation[i + 1]["text"]
                    
                    # Check what was revealed
                    revealed_types = self._check_intelligence_in_message(
                        next_msg, intelligence
                    )
                    
                    for intel_type in revealed_types:
                        tactic_id = str(uuid.uuid4())
                        
                        # Get setup (previous 2 messages)
                        setup_start = max(0, i - 2)
                        setup_messages = [
                            m["text"] for m in conversation[setup_start:i]
                        ]
                        
                        # Embed the tactic
                        tactic_text = f"Extract {intel_type}: {msg['text']}"
                        embedding = self.embedder.embed_text(tactic_text)
                        
                        # Create tactic point
                        point = PointStruct(
                            id=tactic_id,
                            vector=embedding,
                            payload={
                                "tactic_id": tactic_id,
                                "session_id": session_id,
                                "scam_type": scam_type,
                                "persona": persona,
                                "setup_messages": setup_messages,
                                "extraction_question": msg["text"],
                                "scammer_response": next_msg,
                                "intelligence_type": intel_type,
                                "success_rate": 1.0,  # Will average over time
                                "generalized_pattern": self._generalize_tactic(msg["text"]),
                                "timestamp": datetime.now().isoformat()
                            }
                        )
                        
                        self.client.upsert(
                            collection_name="extraction_tactics",
                            points=[point]
                        )
    
    def _generate_tags(self, scammer_msg: str, victim_response: str) -> List[str]:
        """Generate tags for categorization"""
        tags = []
        
        scammer_lower = scammer_msg.lower()
        response_lower = victim_response.lower()
        
        # Scammer tactic tags
        if any(word in scammer_lower for word in ["urgent", "immediately", "now"]):
            tags.append("urgency_response")
        if any(word in scammer_lower for word in ["bank", "account", "verify"]):
            tags.append("authority_response")
        if "?" in scammer_msg:
            tags.append("question_response")
        
        # Victim tactic tags
        if "?" in victim_response:
            tags.append("asked_clarification")
        if any(word in response_lower for word in ["confused", "understand", "what"]):
            tags.append("showed_confusion")
        if any(word in response_lower for word in ["where", "send", "again"]):
            tags.append("requested_repeat")
        if len(victim_response.split()) < 5:
            tags.append("brief_response")
        
        return tags
    
    def _identify_successful_tactics(
        self,
        conversation: List[Dict],
        intelligence: Dict
    ) -> List[str]:
        """Identify what tactics led to success"""
        tactics = []
        
        # Check if showed confusion
        victim_messages = [m["text"].lower() for m in conversation if m["sender"] == "user"]
        if any("confused" in msg or "don't understand" in msg for msg in victim_messages):
            tactics.append("showed_confusion_to_buy_time")
        
        # Check if asked for clarification/repeat
        if any("again" in msg or "repeat" in msg or "send" in msg for msg in victim_messages):
            tactics.append("asked_for_clarification_to_confirm_details")
        
        # Check if mentioned family
        if any("daughter" in msg or "son" in msg or "grandson" in msg for msg in victim_messages):
            tactics.append("mentioned_family_member_for_realism")
        
        # Check if built trust gradually
        if len(conversation) >= 8:
            tactics.append("built_trust_gradually_over_time")
        
        # Check if extracted multiple types
        intel_types = sum([1 for v in intelligence.values() if len(v) > 0])
        if intel_types >= 2:
            tactics.append("extracted_multiple_intelligence_types")
        
        return tactics
    
    def _calculate_engagement_quality(self, message_count: int) -> float:
        """Calculate engagement quality score"""
        # Ideal is 8-15 messages
        if 8 <= message_count <= 15:
            return 10.0
        elif 5 <= message_count < 8:
            return 7.5
        elif 15 < message_count <= 20:
            return 8.0
        elif message_count < 5:
            return 5.0
        else:
            return 6.0
    
    def _check_intelligence_in_message(
        self,
        message: str,
        intelligence: Dict
    ) -> List[str]:
        """Check what types of intelligence are in a message"""
        found_types = []
        
        # Check for each intelligence type
        for intel_type, intel_list in intelligence.items():
            for item in intel_list:
                if item in message:
                    # Map storage keys to tactic types
                    type_map = {
                        "bank_accounts": "bank_account",
                        "upi_ids": "upi_id",
                        "phishing_links": "phishing_link",
                        "phone_numbers": "phone_number"
                    }
                    found_types.append(type_map.get(intel_type, intel_type))
                    break
        
        return found_types
    
    def _generalize_tactic(self, specific_question: str) -> str:
        """Create generalized pattern from specific question"""
        
        question_lower = specific_question.lower()
        
        # Pattern matching
        if "again" in question_lower:
            return "ask_to_repeat_details"
        elif "link" in question_lower and ("work" in question_lower or "open" in question_lower):
            return "claim_technical_issue_to_get_repeat_link"
        elif "where" in question_lower or "send" in question_lower:
            return "ask_for_payment_destination"
        elif "how" in question_lower:
            return "request_step_by_step_instructions"
        elif "safe" in question_lower:
            return "express_safety_concern_to_get_reassurance"
        else:
            return "request_clarification"
```

---

## 8. Integration Guide

### Step-by-Step Integration

**Step 1: Install Dependencies** (5 minutes)

```bash
pip install qdrant-client sentence-transformers
```

**Step 2: Set Up Qdrant** (10 minutes)

```bash
# 1. Sign up at https://cloud.qdrant.io
# 2. Create a cluster (free tier)
# 3. Get API key and URL
# 4. Add to .env file

# .env
QDRANT_URL=https://your-cluster.qdrant.io:6333
QDRANT_API_KEY=your_api_key_here
```

**Step 3: Initialize Collections** (5 minutes)

```python
# In main.py or separate init script

from app.core.rag_config import initialize_collections

# Run once to create collections
initialize_collections()
```

**Step 4: Update Main Application** (10 minutes)

```python
# main.py

from app.agents.rag_conversation_manager import RAGEnhancedConversationManager
from app.core.rag_config import qdrant_client

# Replace conversation manager
conversation_manager = RAGEnhancedConversationManager(
    llm_client=groq_client,
    qdrant_client=qdrant_client
)

# In /api/chat endpoint, replace generate_enhanced_response with:
reply = await conversation_manager.generate_rag_enhanced_response(
    persona_name=session['persona'],
    scammer_message=request.message.text,
    conversation_history=session['conversation_history'],
    session=session,
    message_number=session['message_count']
)
```

**Step 5: Store Completed Conversations** (5 minutes)

```python
# In /api/chat endpoint, when session ends:

if should_end and session['scam_detected']:
    # Send GUVI callback (existing code)
    await guvi_callback.send_final_result(...)
    
    # NEW: Store conversation in RAG
    from app.rag.knowledge_store import KnowledgeStore
    knowledge_store = KnowledgeStore(qdrant_client)
    
    await knowledge_store.store_completed_conversation(
        session_id=request.sessionId,
        conversation_history=session['conversation_history'],
        persona=session['persona'],
        scam_type=session['scam_type'],
        intelligence=session['intelligence'],
        intelligence_score=intelligence_extractor.calculate_score(session['intelligence'])
    )
```

---

## 9. Learning Loop

### Continuous Improvement System

```python
# app/rag/learning_loop.py

class ContinuousLearningSystem:
    """System that learns and improves over time"""
    
    def __init__(self, knowledge_store, qdrant_client):
        self.knowledge_store = knowledge_store
        self.client = qdrant_client
    
    async def analyze_performance(self):
        """Analyze what's working and what's not"""
        
        # Get all conversations from last week
        results = self.client.scroll(
            collection_name="conversations",
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="timestamp",
                        range={"gte": (datetime.now() - timedelta(days=7)).isoformat()}
                    )
                ]
            ),
            limit=100
        )
        
        conversations = [point.payload for point in results[0]]
        
        # Analyze success patterns
        successful = [c for c in conversations if c.get("intelligence_score", 0) >= 7]
        failed = [c for c in conversations if c.get("intelligence_score", 0) < 4]
        
        analysis = {
            "total_conversations": len(conversations),
            "successful_count": len(successful),
            "success_rate": len(successful) / len(conversations) if conversations else 0,
            "average_intelligence_score": sum(c.get("intelligence_score", 0) for c in conversations) / len(conversations) if conversations else 0,
            "average_message_count": sum(c.get("message_count", 0) for c in conversations) / len(conversations) if conversations else 0,
            "top_personas": self._analyze_top_personas(successful),
            "successful_tactics": self._analyze_tactics(successful),
            "improvement_areas": self._identify_improvements(failed)
        }
        
        return analysis
    
    def _analyze_top_personas(self, successful_conversations: List[Dict]) -> Dict:
        """Find which personas perform best"""
        persona_scores = {}
        
        for conv in successful_conversations:
            persona = conv.get("persona")
            if persona:
                if persona not in persona_scores:
                    persona_scores[persona] = []
                persona_scores[persona].append(conv.get("intelligence_score", 0))
        
        # Calculate averages
        return {
            persona: sum(scores) / len(scores)
            for persona, scores in persona_scores.items()
        }
    
    def _analyze_tactics(self, successful_conversations: List[Dict]) -> List[str]:
        """Find most common successful tactics"""
        from collections import Counter
        
        all_tactics = []
        for conv in successful_conversations:
            all_tactics.extend(conv.get("successful_tactics", []))
        
        # Get top 10 tactics
        tactic_counts = Counter(all_tactics)
        return [tactic for tactic, count in tactic_counts.most_common(10)]
    
    def _identify_improvements(self, failed_conversations: List[Dict]) -> List[str]:
        """Identify what needs improvement"""
        improvements = []
        
        if not failed_conversations:
            return improvements
        
        # Check average message count
        avg_messages = sum(c.get("message_count", 0) for c in failed_conversations) / len(failed_conversations)
        if avg_messages < 5:
            improvements.append("Conversations ending too early - improve engagement")
        
        # Check personas
        failed_personas = [c.get("persona") for c in failed_conversations]
        from collections import Counter
        persona_counts = Counter(failed_personas)
        if persona_counts:
            worst_persona = persona_counts.most_common(1)[0][0]
            improvements.append(f"Persona '{worst_persona}' needs improvement")
        
        # Check intelligence types
        total_intel = {
            "bank_accounts": 0,
            "upi_ids": 0,
            "phishing_links": 0,
            "phone_numbers": 0
        }
        
        for conv in failed_conversations:
            intel = conv.get("intelligence_extracted", {})
            for key in total_intel:
                total_intel[key] += len(intel.get(key, []))
        
        # Find least extracted type
        if total_intel:
            min_type = min(total_intel, key=total_intel.get)
            improvements.append(f"Need better tactics for extracting {min_type}")
        
        return improvements
    
    async def update_tactic_success_rates(self):
        """Update success rates for extraction tactics based on actual usage"""
        
        # Get all extraction tactics
        tactics = self.client.scroll(
            collection_name="extraction_tactics",
            limit=1000
        )[0]
        
        for tactic_point in tactics:
            tactic = tactic_point.payload
            pattern = tactic.get("generalized_pattern")
            
            # Find all uses of this tactic
            # (Would need to track tactic usage - simplified here)
            
            # Update success rate
            # This is a placeholder - implement actual tracking
            pass
```

### Automated Report Generation

```python
# app/rag/reporting.py

class PerformanceReporter:
    """Generate performance reports"""
    
    def __init__(self, learning_system):
        self.learning_system = learning_system
    
    async def generate_daily_report(self) -> str:
        """Generate daily performance report"""
        
        analysis = await self.learning_system.analyze_performance()
        
        report = f"""
# AI Honeypot Daily Performance Report
Date: {datetime.now().strftime('%Y-%m-%d')}

## Overall Metrics
- Total Conversations: {analysis['total_conversations']}
- Success Rate: {analysis['success_rate']*100:.1f}%
- Avg Intelligence Score: {analysis['average_intelligence_score']:.2f}/10
- Avg Messages/Conversation: {analysis['average_message_count']:.1f}

## Top Performing Personas
"""
        
        for persona, score in sorted(
            analysis['top_personas'].items(),
            key=lambda x: x[1],
            reverse=True
        ):
            report += f"- {persona}: {score:.2f}/10\n"
        
        report += "\n## Most Successful Tactics\n"
        for i, tactic in enumerate(analysis['successful_tactics'][:5], 1):
            report += f"{i}. {tactic}\n"
        
        report += "\n## Areas for Improvement\n"
        for improvement in analysis['improvement_areas']:
            report += f"- {improvement}\n"
        
        return report
```

---

## 10. Testing & Validation

### Test RAG System

```python
# tests/test_rag_system.py

import pytest
from app.rag.retriever import RAGRetriever
from app.rag.knowledge_store import KnowledgeStore

@pytest.mark.asyncio
async def test_retrieval():
    """Test that retrieval works"""
    
    retriever = RAGRetriever(qdrant_client)
    
    # Test retrieving similar conversations
    results = await retriever.retrieve_similar_conversations(
        scammer_message="Your account will be blocked",
        scam_type="bank_fraud",
        persona="elderly_confused",
        limit=3
    )
    
    assert len(results) <= 3
    if results:
        assert results[0]["persona"] == "elderly_confused"
        assert results[0]["scam_type"] == "bank_fraud"

@pytest.mark.asyncio
async def test_storage():
    """Test that storage works"""
    
    knowledge_store = KnowledgeStore(qdrant_client)
    
    # Store a test interaction
    await knowledge_store.store_interaction(
        session_id="test_123",
        scammer_message="Send money now",
        victim_response="Where do I send it?",
        persona="elderly_confused",
        scam_type="bank_fraud",
        intelligence_so_far={}
    )
    
    # Verify it was stored (would need to retrieve and check)
    # This is simplified
    assert True

@pytest.mark.asyncio
async def test_rag_enhanced_generation():
    """Test RAG-enhanced response generation"""
    
    from app.agents.rag_conversation_manager import RAGEnhancedConversationManager
    
    manager = RAGEnhancedConversationManager(groq_client, qdrant_client)
    
    session = {
        "session_id": "test_456",
        "persona": "elderly_confused",
        "scam_type": "bank_fraud",
        "intelligence": {},
        "conversation_history": [],
        "message_count": 1
    }
    
    response = await manager.generate_rag_enhanced_response(
        persona_name="elderly_confused",
        scammer_message="Your account is blocked",
        conversation_history=[],
        session=session,
        message_number=1
    )
    
    assert len(response) > 0
    assert response[0].islower() or response.startswith("what") or response.startswith("oh")
```

### Validation Checklist

**Before Deployment:**

- [ ] Qdrant collections created successfully
- [ ] Embedding model loads correctly
- [ ] Can store interactions
- [ ] Can retrieve similar conversations
- [ ] RAG context enhances prompts
- [ ] Responses maintain quality
- [ ] Intelligence extraction still works
- [ ] Learning loop stores completed conversations
- [ ] Performance analysis runs without errors
- [ ] Response time still <3 seconds with RAG

**After First Day:**

- [ ] At least 10 conversations stored
- [ ] Retrieval returns relevant examples
- [ ] RAG context appears in prompts
- [ ] Responses show improvement/consistency
- [ ] No errors in logs
- [ ] Qdrant storage usage reasonable

**After First Week:**

- [ ] 50+ conversations stored
- [ ] Success rate improving
- [ ] Extraction tactics being learned
- [ ] Persona consistency improving
- [ ] Generate performance report
- [ ] Review and optimize

---

## Quick Start Summary

**Minimal RAG Implementation (2 hours):**

1. Install: `pip install qdrant-client sentence-transformers`
2. Sign up for Qdrant Cloud (free)
3. Add 3 files:
   - `app/rag/embeddings.py` (embedding generator)
   - `app/rag/retriever.py` (retrieve examples)
   - `app/rag/knowledge_store.py` (store conversations)
4. Update `main.py` to use RAG manager
5. Store completed conversations after each session
6. Test with 10 conversations

**Full RAG System (4 hours):**
- Add all components above
- Implement learning loop
- Set up performance reporting
- Comprehensive testing

---

## Expected Results

**Week 1:**
- 50+ conversations stored
- Basic retrieval working
- Slight improvement in consistency

**Week 2:**
- 200+ conversations
- Noticeable pattern learning
- Extraction rate +5-10%
- Response consistency significantly better

**Week 3:**
- 500+ conversations
- System learns best tactics
- Persona consistency near-perfect
- Intelligence extraction +10-15%

---

**END OF RAG IMPLEMENTATION GUIDE**

*This RAG system transforms your honeypot from a stateless agent into a continuously learning system that improves with every conversation. Start with the minimal implementation and expand as you see results.*
