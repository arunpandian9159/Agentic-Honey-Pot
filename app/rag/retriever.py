"""
RAG Retriever for AI Honeypot.
Retrieves relevant examples from knowledge base to augment LLM context.
"""

import logging
from typing import List, Dict, Optional

from app.rag.embeddings import embedding_generator

logger = logging.getLogger(__name__)


class RAGRetriever:
    """Retrieve relevant examples from knowledge base."""
    
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
        Retrieve similar successful conversations.
        
        Returns conversations where:
        - Similar scam type and message pattern
        - Same persona
        - High intelligence score
        """
        if not self.client:
            return []
        
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue, Range
            
            query_text = f"Scam: {scam_type}. Message: {scammer_message}"
            query_vector = self.embedder.embed_text(query_text)
            
            if not query_vector or not persona:
                return []
            
            # Build filter
            filter_conditions = Filter(
                must=[
                    FieldCondition(
                        key="persona",
                        match=MatchValue(value=persona)
                    ),
                    FieldCondition(
                        key="intelligence_score",
                        range=Range(gte=5.0)
                    )
                ]
            )
            
            # Use query_points API (recommended modern API)
            if hasattr(self.client, "query_points"):
                results = self.client.query_points(
                    collection_name="conversations",
                    query=query_vector,
                    query_filter=filter_conditions,
                    limit=limit
                ).points
            elif hasattr(self.client, "search"):
                results = self.client.search(
                    collection_name="conversations",
                    query_vector=query_vector,
                    query_filter=filter_conditions,
                    limit=limit
                )
            else:
                logger.error(f"Qdrant client missing required methods. Available: {dir(self.client)}")
                return []
            
            return [result.payload for result in results]
        
        except Exception as e:
            logger.error(f"Retrieval error: {e}")
            return []
    
    async def retrieve_response_patterns(
        self,
        scammer_message: str,
        persona: str,
        conversation_stage: str,
        limit: int = 5
    ) -> List[Dict]:
        """
        Retrieve effective response patterns.
        Returns specific responses that worked in similar situations.
        """
        if not self.client:
            return []
        
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            query_text = f"Stage: {conversation_stage}. Scammer: {scammer_message}"
            query_vector = self.embedder.embed_text(query_text)
            
            if not query_vector or not persona:
                return []
            
            filter_conditions = Filter(
                must=[
                    FieldCondition(key="persona", match=MatchValue(value=persona)),
                    FieldCondition(key="led_to_intelligence", match=MatchValue(value=True))
                ]
            )
            
            # Use query_points API
            if hasattr(self.client, "query_points"):
                results = self.client.query_points(
                    collection_name="response_patterns",
                    query=query_vector,
                    query_filter=filter_conditions,
                    limit=limit
                ).points
            elif hasattr(self.client, "search"):
                results = self.client.search(
                    collection_name="response_patterns",
                    query_vector=query_vector,
                    query_filter=filter_conditions,
                    limit=limit
                )
            else:
                logger.error(f"Qdrant client missing required methods. Available: {dir(self.client)}")
                return []
            
            return [result.payload for result in results]
        
        except Exception as e:
            logger.error(f"Pattern retrieval error: {e}")
            return []
    
    async def retrieve_extraction_tactics(
        self,
        scam_type: str,
        persona: str,
        target_intel_type: str,
        limit: int = 3
    ) -> List[Dict]:
        """
        Retrieve successful intelligence extraction tactics.
        Returns proven tactics for extracting specific intel types.
        """
        if not self.client:
            return []
        
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue, Range
            
            query_text = f"Extract {target_intel_type} from {scam_type} as {persona}"
            query_vector = self.embedder.embed_text(query_text)
            
            if not query_vector or not target_intel_type:
                return []
            
            filter_conditions = Filter(
                must=[
                    FieldCondition(key="intelligence_type", match=MatchValue(value=target_intel_type)),
                    FieldCondition(key="success_rate", range=Range(gte=0.6))
                ]
            )
            
            # Use query_points API
            if hasattr(self.client, "query_points"):
                results = self.client.query_points(
                    collection_name="extraction_tactics",
                    query=query_vector,
                    query_filter=filter_conditions,
                    limit=limit
                ).points
            elif hasattr(self.client, "search"):
                results = self.client.search(
                    collection_name="extraction_tactics",
                    query_vector=query_vector,
                    query_filter=filter_conditions,
                    limit=limit
                )
            else:
                logger.error(f"Qdrant client missing required methods. Available: {dir(self.client)}")
                return []
            
            return [result.payload for result in results]
        
        except Exception as e:
            logger.error(f"Tactics retrieval error: {e}")
            return []
    
    async def retrieve_persona_examples(
        self,
        persona: str,
        recent_messages: List[Dict],
        limit: int = 3
    ) -> List[Dict]:
        """
        Retrieve examples to maintain persona consistency.
        Returns conversations where persona was well-maintained.
        """
        if not self.client:
            return []
        
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue, Range
            
            history_text = " ".join([msg.get("text", "") for msg in recent_messages[-3:]])
            query_text = f"Persona: {persona}. Context: {history_text}"
            query_vector = self.embedder.embed_text(query_text)
            
            if not query_vector or not persona:
                return []
            
            filter_conditions = Filter(
                must=[
                    FieldCondition(key="persona", match=MatchValue(value=persona)),
                    FieldCondition(key="persona_consistency", range=Range(gte=8.0))
                ]
            )
            
            # Use query_points API
            if hasattr(self.client, "query_points"):
                results = self.client.query_points(
                    collection_name="conversations",
                    query=query_vector,
                    query_filter=filter_conditions,
                    limit=limit
                ).points
            elif hasattr(self.client, "search"):
                results = self.client.search(
                    collection_name="conversations",
                    query_vector=query_vector,
                    query_filter=filter_conditions,
                    limit=limit
                )
            else:
                logger.error(f"Qdrant client missing required methods. Available: {dir(self.client)}")
                return []
            
            return [result.payload for result in results]
        
        except Exception as e:
            logger.error(f"Persona retrieval error: {e}")
            return []
    
    def format_retrieval_context(self, results: List[Dict], context_type: str) -> str:
        """Format retrieved results for LLM prompt."""
        if not results:
            return ""
        
        formatters = {
            "conversations": self._format_conversation_examples,
            "responses": self._format_response_examples,
            "tactics": self._format_tactic_examples,
            "persona": self._format_persona_examples
        }
        
        formatter = formatters.get(context_type)
        return formatter(results) if formatter else ""
    
    def _format_conversation_examples(self, conversations: List[Dict]) -> str:
        """Format similar conversation examples."""
        formatted = ["SIMILAR SUCCESSFUL CONVERSATIONS:\n"]
        
        for i, conv in enumerate(conversations, 1):
            formatted.append(f"\nExample {i} (Score: {conv.get('intelligence_score', 0)}):")
            full_conv = conv.get('full_conversation', '')[:150]
            formatted.append(full_conv + "...")
            
            tactics = conv.get('successful_tactics', [])
            if tactics:
                formatted.append(f"Worked: {', '.join(tactics[:2])}")
        
        return "\n".join(formatted)
    
    def _format_response_examples(self, responses: List[Dict]) -> str:
        """Format response pattern examples."""
        formatted = ["EFFECTIVE RESPONSE PATTERNS:\n"]
        
        for i, resp in enumerate(responses, 1):
            formatted.append(f'\n{i}. When scammer said: "{resp.get("scammer_message", "")}"')
            formatted.append(f'   Good response: "{resp.get("victim_response", "")}"')
            tags = resp.get('tags', [])
            if tags:
                formatted.append(f"   Why it worked: {', '.join(tags[:2])}")
        
        return "\n".join(formatted)
    
    def _format_tactic_examples(self, tactics: List[Dict]) -> str:
        """Format extraction tactic examples."""
        formatted = ["SUCCESSFUL EXTRACTION TACTICS:\n"]
        
        for i, tactic in enumerate(tactics, 1):
            formatted.append(f"\n{i}. Tactic: {tactic.get('generalized_pattern', '')}")
            formatted.append(f'   Example question: "{tactic.get("extraction_question", "")}"')
            rate = tactic.get('success_rate', 0) * 100
            formatted.append(f"   Success rate: {rate:.0f}%")
        
        return "\n".join(formatted)
    
    def _format_persona_examples(self, examples: List[Dict]) -> str:
        """Format persona consistency examples."""
        formatted = ["PERSONA-CONSISTENT EXAMPLES:\n"]
        
        for i, ex in enumerate(examples, 1):
            victim_responses = ex.get('victim_responses', [])[:1]
            formatted.append(f"\n{i}. Example response: {victim_responses[0] if victim_responses else ''}")
        
        return "\n".join(formatted)
