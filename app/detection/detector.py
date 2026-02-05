"""
Scam Detector Orchestrator for AI Honeypot API.
Orchestrates multiple analyzers to produce a comprehensive detection result.
"""

import logging
import asyncio
from typing import Dict, List, Optional

from app.detection.analyzers.linguistic import LinguisticAnalyzer
from app.detection.analyzers.behavioral import BehavioralAnalyzer
from app.detection.analyzers.technical import TechnicalAnalyzer
from app.detection.analyzers.contextual import ContextAnalyzer
from app.detection.analyzers.llm_analyzer import AdvancedLLMDetector
from app.detection.models.detection_result import DetectionResult, ScamType
from app.detection.config import DETECTION_CONFIG

logger = logging.getLogger(__name__)


class ScamDetector:
    """
    Orchestrates multi-factor scam detection.
    
    Combines results from linguistic, behavioral, technical, contextual, 
    and LLM-based analysis.
    """
    
    def __init__(self, llm_client):
        self.linguistic_analyzer = LinguisticAnalyzer()
        self.behavioral_analyzer = BehavioralAnalyzer()
        self.technical_analyzer = TechnicalAnalyzer()
        self.context_analyzer = ContextAnalyzer()
        self.llm_detector = AdvancedLLMDetector(llm_client)
        
        self.weights = DETECTION_CONFIG["factor_weights"]
        self.confidence_threshold = DETECTION_CONFIG["confidence_threshold"]
        self.llm_high_confidence = DETECTION_CONFIG["llm_high_confidence_threshold"]
    
    async def analyze(
        self,
        message: str,
        history: List[Dict] = None,
        metadata: Dict = None
    ) -> DetectionResult:
        """
        Run multi-factor analysis on a message.
        """
        if metadata is None:
            metadata = {}
        if history is None:
            history = []
            
        logger.info(f"Running multi-factor detection for message: {message[:50]}...")
        
        try:
            # Run LLM analysis (it is async)
            llm_result = await self.llm_detector.analyze(message, metadata, history)
            
            # Run synchronous analyzers
            ling_result = self.linguistic_analyzer.analyze(message)
            beh_result = self.behavioral_analyzer.analyze(message, metadata)
            tech_result = self.technical_analyzer.analyze(message)
            ctx_result = self.context_analyzer.analyze(message, metadata, history)
            
            # Combine all results
            return self._combine_results(
                ling_result, beh_result, tech_result, ctx_result, llm_result, message
            )
            
        except Exception as e:
            logger.error(f"Error during scam detection: {str(e)}", exc_info=True)
            # Return a neutral/uncertain result on failure
            return DetectionResult(
                is_scam=False,
                confidence=0.5,
                scam_type=None,
                reasoning=f"Detection error: {str(e)}",
                red_flags=[],
                legitimacy_signals=[],
                factors={},
                analyzer_results={}
            )

    def _combine_results(
        self, 
        ling: Dict, 
        beh: Dict, 
        tech: Dict, 
        ctx: Dict, 
        llm: Dict, 
        message: str
    ) -> DetectionResult:
        """Combine results from all factors into a final DetectionResult."""
        
        # Extract individual scores
        factor_scores = {
            "linguistic": ling.get("overall_linguistic_score", 0.0),
            "behavioral": beh.get("overall_behavioral_score", 0.0),
            "technical": tech.get("overall_technical_score", 0.0),
            "context": ctx.get("overall_context_score", 0.0),
            "llm": self._calculate_llm_score(llm)
        }
        
        # Calculate weighted overall score
        overall_score = sum(
            factor_scores[factor] * self.weights[factor]
            for factor in self.weights.keys()
        )
        
        # Make final decision based on weighted score
        is_scam = overall_score >= self.confidence_threshold
        
        # Handle LLM Overrides
        llm_confidence = llm.get("confidence", 0.5)
        llm_is_scam = llm.get("is_scam")
        
        # 1. If LLM is very confident, trust it more
        if llm_confidence >= self.llm_high_confidence:
            is_scam = bool(llm_is_scam) if llm_is_scam is not None else is_scam
            overall_score = llm_confidence if is_scam else (1 - llm_confidence)
            
        # 2. If weighted score is low but LLM is confident about a scam
        elif llm_is_scam and llm_confidence >= self.confidence_threshold:
            is_scam = True
            overall_score = max(overall_score, llm_confidence)

        # Map string scam type to Enum
        scam_type_str = llm.get("scam_type", "other")
        try:
            scam_type = ScamType(scam_type_str)
        except ValueError:
            scam_type = ScamType.OTHER
            
        # Collect Red Flags
        red_flags = self._collect_red_flags(ling, beh, tech, ctx, llm)
        
        result = DetectionResult(
            is_scam=is_scam,
            confidence=overall_score,
            scam_type=scam_type if is_scam else None,
            reasoning=llm.get("reasoning", "Combined factor analysis"),
            red_flags=red_flags,
            legitimacy_signals=llm.get("legitimacy_signals", []),
            factors=factor_scores,
            analyzer_results={
                "linguistic": ling,
                "behavioral": beh,
                "technical": tech,
                "context": ctx,
                "llm": llm
            }
        )
        
        logger.info(f"Final Detection Result: is_scam={result.is_scam}, confidence={result.confidence:.2f}")
        return result

    def _calculate_llm_score(self, llm: Dict) -> float:
        """Calculate LLM contribution to score."""
        if llm.get("is_scam") is None:
            return 0.5
        
        confidence = llm.get("confidence", 0.5)
        if llm.get("is_scam"):
            return confidence
        else:
            return 1.0 - confidence

    def _collect_red_flags(self, ling: Dict, beh: Dict, tech: Dict, ctx: Dict, llm: Dict) -> List[str]:
        """Collect red flags from all analyzers."""
        flags = []
        threshold = DETECTION_CONFIG.get("red_flag_threshold", 0.6)
        
        if ling.get("urgency_score", 0) >= threshold: flags.append("Urgent language")
        if ling.get("threat_score", 0) >= threshold: flags.append("Threatening content")
        if beh.get("payment_demand_score", 0) >= threshold: flags.append("Payment request")
        if beh.get("information_request_score", 0) >= threshold: flags.append("Info request")
        if tech.get("overall_technical_score", 0) >= threshold: flags.append("Suspicious technical signals")
        
        # Merge LLM red flags
        if llm.get("red_flags"):
            for flag in llm["red_flags"]:
                if flag not in flags:
                    flags.append(flag)
                    
        return flags