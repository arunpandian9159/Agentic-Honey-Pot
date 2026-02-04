"""
Knowledge Store for RAG system.
Stores new learnings in vector database for future retrieval.
"""

import uuid
import logging
from datetime import datetime
from typing import Dict, List

from app.rag.embeddings import embedding_generator

logger = logging.getLogger(__name__)


class KnowledgeStore:
    """Store new learnings in RAG knowledge base."""
    
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
        """Store single interaction as response pattern."""
        if not self.client:
            return
        
        try:
            from qdrant_client.models import PointStruct
            
            pattern_id = str(uuid.uuid4())
            
            # Embed the interaction
            interaction_text = f"Scammer: {scammer_message}\nVictim: {victim_response}"
            embedding = self.embedder.embed_text(interaction_text)
            
            if not embedding:
                return
            
            # Determine if this led to intelligence
            led_to_intel = any(
                len(v) > 0 for v in intelligence_so_far.values() if isinstance(v, list)
            )
            
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
                    "maintained_persona": True,
                    "tags": self._generate_tags(scammer_message, victim_response)
                }
            )
            
            self.client.upsert(
                collection_name="response_patterns",
                points=[point]
            )
            logger.debug(f"Stored response pattern: {pattern_id}")
        
        except Exception as e:
            logger.error(f"Failed to store interaction: {e}")
    
    async def store_completed_conversation(
        self,
        session_id: str,
        conversation_history: List[Dict],
        persona: str,
        scam_type: str,
        intelligence: Dict,
        intelligence_score: float
    ):
        """Store complete conversation after session ends."""
        if not self.client:
            return
        
        try:
            from qdrant_client.models import PointStruct
            
            conv_id = str(uuid.uuid4())
            
            # Format full conversation
            full_conversation = "\n".join([
                f"{'Scammer' if msg.get('sender') == 'scammer' else 'Victim'}: {msg.get('text', '')}"
                for msg in conversation_history
            ])
            
            embedding = self.embedder.embed_text(full_conversation)
            if not embedding:
                return
            
            # Extract messages by sender
            victim_responses = [
                msg.get("text", "") for msg in conversation_history
                if msg.get("sender") == "user"
            ]
            scammer_messages = [
                msg.get("text", "") for msg in conversation_history
                if msg.get("sender") == "scammer"
            ]
            
            # Identify successful tactics
            tactics = self._identify_successful_tactics(conversation_history, intelligence)
            
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
                    "scammer_messages": scammer_messages,
                    "intelligence_extracted": intelligence,
                    "intelligence_score": intelligence_score,
                    "engagement_quality": self._calculate_engagement_quality(len(conversation_history)),
                    "extraction_success": intelligence_score >= 5.0,
                    "successful_tactics": tactics,
                    "persona_consistency": 8.5,
                    "human_likeness": 9.0
                }
            )
            
            self.client.upsert(
                collection_name="conversations",
                points=[point]
            )
            logger.info(f"Stored conversation: {conv_id} (score: {intelligence_score})")
            
            # Store extraction tactics if successful
            if intelligence_score >= 5.0:
                await self._store_extraction_tactics(
                    session_id, conversation_history, persona, scam_type, intelligence
                )
        
        except Exception as e:
            logger.error(f"Failed to store conversation: {e}")
    
    async def _store_extraction_tactics(
        self,
        session_id: str,
        conversation: List[Dict],
        persona: str,
        scam_type: str,
        intelligence: Dict
    ):
        """Extract and store successful extraction tactics."""
        try:
            from qdrant_client.models import PointStruct
            
            for i, msg in enumerate(conversation):
                if msg.get("sender") == "user":
                    if i + 1 < len(conversation):
                        next_msg = conversation[i + 1].get("text", "")
                        
                        # Check what was revealed
                        revealed_types = self._check_intelligence_in_message(next_msg, intelligence)
                        
                        for intel_type in revealed_types:
                            tactic_id = str(uuid.uuid4())
                            
                            # Get setup messages
                            setup_start = max(0, i - 2)
                            setup_messages = [
                                m.get("text", "") for m in conversation[setup_start:i]
                            ]
                            
                            tactic_text = f"Extract {intel_type}: {msg.get('text', '')}"
                            embedding = self.embedder.embed_text(tactic_text)
                            
                            if not embedding:
                                continue
                            
                            point = PointStruct(
                                id=tactic_id,
                                vector=embedding,
                                payload={
                                    "tactic_id": tactic_id,
                                    "session_id": session_id,
                                    "scam_type": scam_type,
                                    "persona": persona,
                                    "setup_messages": setup_messages,
                                    "extraction_question": msg.get("text", ""),
                                    "scammer_response": next_msg,
                                    "intelligence_type": intel_type,
                                    "success_rate": 1.0,
                                    "generalized_pattern": self._generalize_tactic(msg.get("text", "")),
                                    "timestamp": datetime.now().isoformat()
                                }
                            )
                            
                            self.client.upsert(
                                collection_name="extraction_tactics",
                                points=[point]
                            )
                            logger.debug(f"Stored extraction tactic: {tactic_id}")
        
        except Exception as e:
            logger.error(f"Failed to store tactics: {e}")
    
    def _generate_tags(self, scammer_msg: str, victim_response: str) -> List[str]:
        """Generate tags for categorization."""
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
    
    def _identify_successful_tactics(self, conversation: List[Dict], intelligence: Dict) -> List[str]:
        """Identify what tactics led to success."""
        tactics = []
        
        victim_messages = [m.get("text", "").lower() for m in conversation if m.get("sender") == "user"]
        
        if any("confused" in msg or "don't understand" in msg for msg in victim_messages):
            tactics.append("showed_confusion_to_buy_time")
        
        if any("again" in msg or "repeat" in msg or "send" in msg for msg in victim_messages):
            tactics.append("asked_for_clarification_to_confirm_details")
        
        if any(word in " ".join(victim_messages) for word in ["daughter", "son", "grandson"]):
            tactics.append("mentioned_family_member_for_realism")
        
        if len(conversation) >= 8:
            tactics.append("built_trust_gradually_over_time")
        
        intel_types = sum(1 for v in intelligence.values() if isinstance(v, list) and len(v) > 0)
        if intel_types >= 2:
            tactics.append("extracted_multiple_intelligence_types")
        
        return tactics
    
    def _calculate_engagement_quality(self, message_count: int) -> float:
        """Calculate engagement quality score."""
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
    
    def _check_intelligence_in_message(self, message: str, intelligence: Dict) -> List[str]:
        """Check what types of intelligence are in a message."""
        found_types = []
        
        type_map = {
            "bank_accounts": "bank_account",
            "upi_ids": "upi_id",
            "phishing_links": "phishing_link",
            "phone_numbers": "phone_number"
        }
        
        for intel_type, intel_list in intelligence.items():
            if isinstance(intel_list, list):
                for item in intel_list:
                    if item in message:
                        found_types.append(type_map.get(intel_type, intel_type))
                        break
        
        return found_types
    
    def _generalize_tactic(self, specific_question: str) -> str:
        """Create generalized pattern from specific question."""
        question_lower = specific_question.lower()
        
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
