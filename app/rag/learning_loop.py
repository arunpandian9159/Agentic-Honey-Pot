"""
Continuous Learning System for RAG.
Analyzes performance and identifies improvement areas.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List
from collections import Counter

logger = logging.getLogger(__name__)


class ContinuousLearningSystem:
    """System that learns and improves over time."""
    
    def __init__(self, qdrant_client):
        self.client = qdrant_client
    
    async def analyze_performance(self, days: int = 7) -> Dict:
        """Analyze what's working and what's not."""
        if not self.client:
            return {"error": "Qdrant not connected"}
        
        try:
            # Get conversations from the time period
            results = self.client.scroll(
                collection_name="conversations",
                limit=100
            )
            
            conversations = [point.payload for point in results[0]]
            
            if not conversations:
                return {
                    "total_conversations": 0,
                    "message": "No conversations stored yet"
                }
            
            # Analyze success patterns
            successful = [c for c in conversations if c.get("intelligence_score", 0) >= 7]
            failed = [c for c in conversations if c.get("intelligence_score", 0) < 4]
            
            analysis = {
                "total_conversations": len(conversations),
                "successful_count": len(successful),
                "failed_count": len(failed),
                "success_rate": len(successful) / len(conversations) if conversations else 0,
                "average_intelligence_score": sum(
                    c.get("intelligence_score", 0) for c in conversations
                ) / len(conversations) if conversations else 0,
                "average_message_count": sum(
                    c.get("message_count", 0) for c in conversations
                ) / len(conversations) if conversations else 0,
                "top_personas": self._analyze_top_personas(successful),
                "successful_tactics": self._analyze_tactics(successful),
                "improvement_areas": self._identify_improvements(failed)
            }
            
            return analysis
        
        except Exception as e:
            logger.error(f"Performance analysis failed: {e}")
            return {"error": str(e)}
    
    def _analyze_top_personas(self, successful_conversations: List[Dict]) -> Dict[str, float]:
        """Find which personas perform best."""
        persona_scores: Dict[str, List[float]] = {}
        
        for conv in successful_conversations:
            persona = conv.get("persona")
            if persona:
                if persona not in persona_scores:
                    persona_scores[persona] = []
                persona_scores[persona].append(conv.get("intelligence_score", 0))
        
        return {
            persona: sum(scores) / len(scores)
            for persona, scores in persona_scores.items()
        }
    
    def _analyze_tactics(self, successful_conversations: List[Dict]) -> List[str]:
        """Find most common successful tactics."""
        all_tactics = []
        for conv in successful_conversations:
            all_tactics.extend(conv.get("successful_tactics", []))
        
        tactic_counts = Counter(all_tactics)
        return [tactic for tactic, count in tactic_counts.most_common(10)]
    
    def _identify_improvements(self, failed_conversations: List[Dict]) -> List[str]:
        """Identify what needs improvement."""
        improvements = []
        
        if not failed_conversations:
            return ["No failed conversations - system performing well"]
        
        # Check average message count
        avg_messages = sum(
            c.get("message_count", 0) for c in failed_conversations
        ) / len(failed_conversations)
        
        if avg_messages < 5:
            improvements.append("Conversations ending too early - improve engagement")
        
        # Check personas
        failed_personas = [c.get("persona") for c in failed_conversations]
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
                if isinstance(intel.get(key), list):
                    total_intel[key] += len(intel[key])
        
        if total_intel:
            min_type = min(total_intel, key=total_intel.get)
            improvements.append(f"Need better tactics for extracting {min_type}")
        
        return improvements
    
    async def get_collection_stats(self) -> Dict:
        """Get statistics about RAG collections."""
        if not self.client:
            return {"error": "Qdrant not connected"}
        
        stats = {}
        collections = ["conversations", "response_patterns", "extraction_tactics"]
        
        for name in collections:
            try:
                info = self.client.get_collection(name)
                stats[name] = {
                    "points_count": info.points_count,
                    "vectors_count": info.vectors_count
                }
            except Exception as e:
                stats[name] = {"error": str(e)}
        
        return stats
