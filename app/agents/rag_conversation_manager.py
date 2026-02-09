"""
RAG-Enhanced Conversation Manager for AI Honeypot.
Extends EnhancedConversationManager with RAG capabilities for continuous learning.
"""

import logging
import time
from typing import Dict, List, Optional

from app.agents.enhanced_conversation import EnhancedConversationManager
from app.core.llm import GroqClient

logger = logging.getLogger(__name__)


class RAGEnhancedConversationManager(EnhancedConversationManager):
    """Enhanced conversation manager with RAG capabilities."""
    
    def __init__(self, llm_client: GroqClient, qdrant_client=None):
        super().__init__(llm_client)
        self.qdrant_client = qdrant_client
        self._retriever = None
        self._knowledge_store = None
        
        if qdrant_client:
            self._init_rag_components()
    
    def _init_rag_components(self):
        """Initialize RAG components lazily."""
        try:
            from app.rag.retriever import RAGRetriever
            from app.rag.knowledge_store import KnowledgeStore
            
            self._retriever = RAGRetriever(self.qdrant_client)
            self._knowledge_store = KnowledgeStore(self.qdrant_client)
            logger.info("✓ RAG components initialized")
        except Exception as e:
            logger.warning(f"RAG components unavailable: {e}")
    
    async def process_message(
        self,
        scammer_message: str,
        session: Dict,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Process message with optional RAG enhancement.
        Falls back to base implementation if RAG unavailable.
        """
        # Get RAG context if available
        rag_context = ""
        if self._retriever:
            try:
                rag_context = await self._build_rag_context(
                    scammer_message=scammer_message,
                    session=session
                )
            except Exception as e:
                logger.debug(f"RAG context unavailable: {e}")
        
        # Store RAG context in session for prompt building
        session["_rag_context"] = rag_context
        
        # Call parent implementation (now with RAG context available)
        result = await super().process_message(scammer_message, session, metadata)
        
        # Store interaction for learning
        if self._knowledge_store and result.get("is_scam"):
            try:
                await self._knowledge_store.store_interaction(
                    session_id=session.get("session_id", "unknown"),
                    scammer_message=scammer_message,
                    victim_response=result.get("response", ""),
                    persona=result.get("persona", "unknown"),
                    scam_type=result.get("scam_type", "unknown"),
                    intelligence_so_far=session.get("intelligence", {})
                )
            except Exception as e:
                logger.debug(f"Failed to store interaction: {e}")
        
        return result
    
    async def _build_rag_context(
        self,
        scammer_message: str,
        session: Dict
    ) -> str:
        """Build RAG context from retrieved examples."""
        if not self._retriever:
            return ""
        
        persona_name = session.get("persona") or "tech_naive_parent"
        scam_type = session.get("scam_type") or "unknown"
        message_number = session.get("message_count", 0) + 1
        
        context_parts = []
        
        try:
            # 1. Retrieve effective response patterns
            stage = self._determine_stage(message_number)
            rag_t1 = time.time()
            patterns = await self._retriever.retrieve_response_patterns(
                scammer_message=scammer_message,
                persona=persona_name,
                conversation_stage=stage,
                limit=3
            )
            rag_t2 = time.time()
            logger.debug(f"RAG patterns retrieval: {rag_t2-rag_t1:.3f}s ({len(patterns)} results)")
            if patterns:
                formatted = self._retriever.format_retrieval_context(patterns, "responses")
                context_parts.append(formatted)
            
            # 2. Retrieve extraction tactics (if in extraction phase)
            if message_number >= 6:
                missing_intel = self._identify_missing_intelligence(
                    session.get("intelligence", {})
                )
                rag_t3 = time.time()
                for intel_type in missing_intel[:1]:  # Top priority only
                    tactics = await self._retriever.retrieve_extraction_tactics(
                        scam_type=scam_type,
                        persona=persona_name,
                        target_intel_type=intel_type,
                        limit=2
                    )
                    if tactics:
                        formatted = self._retriever.format_retrieval_context(tactics, "tactics")
                        context_parts.append(formatted)
                rag_t4 = time.time()
                logger.debug(f"RAG tactics retrieval: {rag_t4-rag_t3:.3f}s")
            
            # 3. Retrieve persona consistency examples (after message 4)
            if message_number >= 4:
                history = session.get("conversation_history", [])
                rag_t5 = time.time()
                examples = await self._retriever.retrieve_persona_examples(
                    persona=persona_name,
                    recent_messages=history[-5:],
                    limit=2
                )
                rag_t6 = time.time()
                logger.debug(f"RAG persona retrieval: {rag_t6-rag_t5:.3f}s ({len(examples)} results)")
                if examples:
                    formatted = self._retriever.format_retrieval_context(examples, "persona")
                    context_parts.append(formatted)
        
        except Exception as e:
            logger.debug(f"RAG retrieval error: {e}")
        
        if not context_parts:
            return ""
        
        return "\n\n═══ LEARNED PATTERNS ═══\n" + "\n\n".join(context_parts)
    
    def _determine_stage(self, message_number: int) -> str:
        """Determine conversation stage."""
        if message_number <= 2:
            return "initial"
        elif message_number <= 5:
            return "engagement"
        elif message_number <= 10:
            return "extraction"
        else:
            return "prolongation"
    
    def _identify_missing_intelligence(self, intelligence: Dict) -> List[str]:
        """Identify what intelligence is still missing."""
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
    
    async def store_completed_conversation(self, session: Dict, intelligence_score: float):
        """Store completed conversation for learning."""
        if not self._knowledge_store:
            return
        
        try:
            await self._knowledge_store.store_completed_conversation(
                session_id=session.get("session_id", "unknown"),
                conversation_history=session.get("conversation_history", []),
                persona=session.get("persona", "unknown"),
                scam_type=session.get("scam_type", "unknown"),
                intelligence=session.get("intelligence", {}),
                intelligence_score=intelligence_score
            )
        except Exception as e:
            logger.error(f"Failed to store conversation: {e}")
    
    def _build_enhanced_prompt(
        self,
        scammer_message: str,
        session: Dict,
        persona: Dict,
        message_number: int
    ) -> str:
        """Override to include RAG context in prompt."""
        # Get base prompt from parent
        base_prompt = super()._build_enhanced_prompt(
            scammer_message, session, persona, message_number
        )
        
        # Append RAG context if available
        rag_context = session.get("_rag_context", "")
        if rag_context:
            base_prompt = base_prompt + "\n" + rag_context + "\n\nUse patterns above as guidance. Adapt, don't copy."
        
        return base_prompt
