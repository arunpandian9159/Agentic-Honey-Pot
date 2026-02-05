"""
Enhanced Scam Detector - Multi-factor detection system.

Combines linguistic, behavioral, technical, context, and LLM analysis
to produce accurate scam detection with low false positives.
"""

import logging
from typing import Dict, List, Optional

from app.detection.analyzers.linguistic import LinguisticAnalyzer
from app.detection.analyzers.behavioral import BehavioralAnalyzer
from app.detection.analyzers.technical import TechnicalAnalyzer
from app.detection.analyzers.contextual import ContextAnalyzer
from app.detection.analyzers.llm_analyzer import AdvancedLLMDetector
from app.detection.config import DETECTION_CONFIG

logger = logging.getLogger(__name__)


class EnhancedScamDetector:
    """
    Multi-factor scam detection system.
    
    Combines:
    - Linguistic analysis (urgency, threats, authority, manipulation)
    - Behavioral analysis (info requests, payment demands, time pressure)
    - Technical analysis (URLs, domains, link shorteners)
    - Context analysis (expected communication, timing, channel)
    - LLM-based reasoning (comprehensive pattern understanding)
    
    To produce accurate scam detection with low false positives.
    """
    
    def __init__(self, llm_client):
        self.linguistic_analyzer = LinguisticAnalyzer()
        self.behavioral_analyzer = BehavioralAnalyzer()
        self.technical_analyzer = TechnicalAnalyzer()
        self.context_analyzer = ContextAnalyzer()
        self.llm_detector = AdvancedLLMDetector(llm_client)
        
        # Factor weights from config
        self.weights = DETECTION_CONFIG["factor_weights"]
        self.confidence_threshold = DETECTION_CONFIG["confidence_threshold"]
        self.llm_high_confidence = DETECTION_CONFIG["llm_high_confidence_threshold"]
    
    async def analyze(
        self,
        message: str,
        metadata: Dict = None,
        conversation_history: List[Dict] = None
    ) -> Dict:
        """
        Comprehensive scam analysis using multi-factor detection.
        
        Args:
            message: The message to analyze
            metadata: Request metadata (channel, timestamp, etc.)
            conversation_history: Previous messages in conversation
        
        Returns:
            {
                "is_scam": bool,
                "confidence": float (0.0-1.0),
                "scam_type": str,
                "overall_score": float (0.0-1.0),
                "factor_scores": {...},
                "reasoning": str,
                "red_flags": [...],
                "legitimacy_signals": [...],
                "urgency_level": str
            }
        """
        if metadata is None:
            metadata = {}
        
        if conversation_history is None:
            conversation_history = []
        
        logger.info(f"Enhanced detection analyzing: {message[:50]}...")
        
        try:
            # Run all analyzers
            # Linguistic analysis
            linguistic_result = self.linguistic_analyzer.analyze(message)
            
            # Behavioral analysis
            behavioral_result = self.behavioral_analyzer.analyze(message, metadata)
            
            # Technical analysis
            technical_result = self.technical_analyzer.analyze(message)
            
            # Context analysis
            context_result = self.context_analyzer.analyze(
                message, metadata, conversation_history
            )
            
            # LLM analysis (most comprehensive)
            llm_result = await self.llm_detector.analyze(
                message, metadata, conversation_history
            )
            
        except Exception as e:
            logger.error(f"Error in scam analysis: {str(e)}")
            # Return conservative estimate
            return self._get_fallback_result(message)
        
        # Combine results
        final_result = self._combine_results(
            linguistic_result,
            behavioral_result,
            technical_result,
            context_result,
            llm_result,
            message
        )
        
        logger.info(
            f"Enhanced detection result: is_scam={final_result['is_scam']}, "
            f"confidence={final_result['confidence']:.2f}, "
            f"type={final_result['scam_type']}"
        )
        
        return final_result
    
    def _combine_results(
        self,
        linguistic: Dict,
        behavioral: Dict,
        technical: Dict,
        context: Dict,
        llm: Dict,
        message: str
    ) -> Dict:
        """Combine all analysis results into final decision."""
        
        # Extract scores from each analyzer
        factor_scores = {
            "linguistic": linguistic.get("overall_linguistic_score", 0.0),
            "behavioral": behavioral.get("overall_behavioral_score", 0.0),
            "technical": technical.get("overall_technical_score", 0.0),
            "context": context.get("overall_context_score", 0.0),
            "llm": self._calculate_llm_score(llm)
        }
        
        # Calculate weighted overall score
        overall_score = sum(
            factor_scores[factor] * self.weights[factor]
            for factor in self.weights.keys()
        )
        
        # Make final decision
        is_scam = overall_score >= self.confidence_threshold
        
        llm_confidence = llm.get("confidence", 0.5)
        llm_is_scam = llm.get("is_scam")
        if llm_is_scam is not None and llm_confidence >= self.confidence_threshold:
            if llm_is_scam:
                is_scam = True
                overall_score = max(overall_score, llm_confidence)
            else:
                is_scam = False
                overall_score = min(overall_score, 1 - llm_confidence)
        
        # If LLM is very confident, trust it more
        if llm_confidence >= self.llm_high_confidence:
            is_scam = llm_is_scam if llm_is_scam is not None else is_scam
            overall_score = llm_confidence if llm_is_scam else (1 - llm_confidence)
        
        # Collect red flags and legitimacy signals
        red_flags = self._collect_red_flags(
            linguistic, behavioral, technical, context, llm
        )
        
        legitimacy_signals = llm.get("legitimacy_signals", [])
        
        # Determine scam type
        scam_type = self._determine_scam_type(message, llm, red_flags)
        
        # Determine urgency level
        urgency_level = self._determine_urgency(linguistic, behavioral)
        
        # Build reasoning
        reasoning = self._build_reasoning(
            is_scam, overall_score, factor_scores, red_flags, legitimacy_signals, llm
        )
        
        return {
            "is_scam": is_scam,
            "confidence": overall_score,
            "scam_type": scam_type,
            "overall_score": overall_score,
            "factor_scores": factor_scores,
            "detailed_scores": {
                "linguistic": linguistic,
                "behavioral": behavioral,
                "technical": technical,
                "context": context
            },
            "reasoning": reasoning,
            "red_flags": red_flags,
            "legitimacy_signals": legitimacy_signals,
            "urgency_level": urgency_level,
            "key_indicators": red_flags[:5],  # For backward compatibility
            "llm_analysis": llm.get("reasoning", "")
        }
    
    def _calculate_llm_score(self, llm: Dict) -> float:
        """Calculate LLM contribution to score."""
        if llm.get("is_scam") is None:
            return 0.5  # Uncertain
        
        confidence = llm.get("confidence", 0.5)
        if llm.get("is_scam"):
            return confidence
        else:
            return 1.0 - confidence
    
    def _collect_red_flags(
        self,
        linguistic: Dict,
        behavioral: Dict,
        technical: Dict,
        context: Dict,
        llm: Dict
    ) -> List[str]:
        """Collect all red flags from different analyzers."""
        
        red_flags = []
        threshold = DETECTION_CONFIG["red_flag_threshold"]
        
        # Linguistic red flags
        if linguistic.get("urgency_score", 0) > threshold:
            red_flags.append("High urgency language detected")
        if linguistic.get("threat_score", 0) > threshold:
            red_flags.append("Threatening language detected")
        if linguistic.get("authority_score", 0) > threshold:
            red_flags.append("Authority impersonation detected")
        if linguistic.get("manipulation_score", 0) > threshold:
            red_flags.append("Emotional manipulation detected")
        
        # Behavioral red flags
        if behavioral.get("information_request_score", 0) > 0.7:
            red_flags.append("Requests sensitive personal information")
        if behavioral.get("payment_demand_score", 0) > 0.7:
            red_flags.append("Demands payment or money transfer")
        if behavioral.get("secrecy_score", 0) > 0.5:
            red_flags.append("Requests secrecy or confidentiality")
        if behavioral.get("time_pressure_score", 0) > threshold:
            red_flags.append("Creates artificial time pressure")
        
        # Technical red flags
        if technical.get("url_score", 0) > threshold:
            red_flags.append("Suspicious URL structure detected")
        if technical.get("domain_score", 0) > threshold:
            red_flags.append("Suspicious domain or link shortener detected")
        
        # Context red flags
        if context.get("expected_communication_score", 0) > 0.7:
            red_flags.append("Unsolicited/unexpected communication")
        if context.get("channel_score", 0) > 0.7:
            red_flags.append("Inappropriate channel for sensitive request")
        
        # Add LLM-identified red flags
        if llm.get("red_flags"):
            for flag in llm["red_flags"]:
                if flag not in red_flags:
                    red_flags.append(flag)
        
        # Deduplicate and return
        return list(dict.fromkeys(red_flags))
    
    def _determine_scam_type(
        self,
        message: str,
        llm: Dict,
        red_flags: List[str]
    ) -> str:
        """Determine type of scam."""
        
        # Trust LLM's classification if available
        if llm.get("scam_type") and llm.get("scam_type") not in ["unknown", "legitimate"]:
            return llm["scam_type"]
        
        # Otherwise, infer from keywords
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['bank', 'kyc', 'blocked', 'suspended']):
            return "bank_fraud"
        
        if any(word in message_lower for word in ['upi', 'paytm', 'phonepe', 'googlepay', '@']):
            return "upi_fraud"
        
        if 'http' in message_lower or 'www' in message_lower or 'link' in message_lower:
            return "phishing"
        
        if any(word in message_lower for word in ['job', 'hiring', 'selected', 'position', 'work from home']):
            return "job_scam"
        
        if any(word in message_lower for word in ['won', 'prize', 'winner', 'lottery', 'lucky draw']):
            return "lottery"
        
        if any(word in message_lower for word in ['invest', 'profit', 'return', 'trading', 'crypto']):
            return "investment"
        
        if any(word in message_lower for word in ['virus', 'hacked', 'microsoft', 'apple', 'tech support']):
            return "tech_support"
        
        return "other"
    
    def _determine_urgency(self, linguistic: Dict, behavioral: Dict) -> str:
        """Determine urgency level."""
        urgency_score = linguistic.get("urgency_score", 0)
        threat_score = linguistic.get("threat_score", 0)
        time_pressure = behavioral.get("time_pressure_score", 0)
        
        combined = (urgency_score + threat_score + time_pressure) / 3
        
        if combined >= 0.7:
            return "critical"
        elif combined >= 0.5:
            return "high"
        elif combined >= 0.3:
            return "medium"
        else:
            return "low"
    
    def _build_reasoning(
        self,
        is_scam: bool,
        confidence: float,
        factor_scores: Dict,
        red_flags: List[str],
        legitimacy_signals: List[str],
        llm: Dict
    ) -> str:
        """Build human-readable reasoning."""
        
        if is_scam:
            reasoning = f"Classified as SCAM with {confidence*100:.0f}% confidence. "
            
            # Mention top contributing factors
            top_factors = sorted(
                factor_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )[:2]
            
            factor_names = [f"{name} analysis" for name, score in top_factors if score > 0.5]
            if factor_names:
                reasoning += f"Primary indicators: {', '.join(factor_names)}. "
            
            # Mention key red flags
            if red_flags:
                top_flags = red_flags[:3]
                reasoning += f"Red flags: {', '.join(top_flags)}."
        
        else:
            reasoning = f"Classified as LEGITIMATE with {(1-confidence)*100:.0f}% confidence. "
            
            if legitimacy_signals:
                reasoning += f"Legitimacy indicators: {', '.join(legitimacy_signals[:2])}."
            else:
                reasoning += "No significant scam indicators detected."
        
        # Add LLM reasoning if available
        if llm.get("reasoning"):
            reasoning += f" LLM: {llm['reasoning']}"
        
        return reasoning
    
    def _get_fallback_result(self, message: str) -> Dict:
        """Fallback result when analysis fails."""
        return {
            "is_scam": None,
            "confidence": 0.5,
            "scam_type": "unknown",
            "overall_score": 0.5,
            "factor_scores": {},
            "detailed_scores": {},
            "reasoning": "Analysis failed, uncertain classification",
            "red_flags": [],
            "legitimacy_signals": [],
            "urgency_level": "medium",
            "key_indicators": [],
            "llm_analysis": "Error in analysis"
        }
