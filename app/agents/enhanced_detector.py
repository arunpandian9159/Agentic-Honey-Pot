"""
Enhanced Scam Detector - Multi-factor detection system.

Combines linguistic, behavioral, technical, context, and LLM analysis
to produce accurate scam detection with low false positives.
"""

import logging
from typing import Dict, List, Optional

from app.detectors.linguistic_analyzer import LinguisticAnalyzer
from app.detectors.behavioral_analyzer import BehavioralAnalyzer
from app.detectors.technical_analyzer import TechnicalAnalyzer
from app.detectors.context_analyzer import ContextAnalyzer
from app.detectors.llm_detector import AdvancedLLMDetector
from app.core.detection_config import DETECTION_CONFIG

logger = logging.getLogger(__name__)

# Keyword-to-scam-type mapping for fallback classification
SCAM_TYPE_KEYWORDS = {
    "bank_fraud": ["bank", "kyc", "blocked", "suspended"],
    "upi_fraud": ["upi", "paytm", "phonepe", "googlepay", "@"],
    "phishing": ["http", "www", "link"],
    "job_scam": ["job", "hiring", "selected", "position", "work from home"],
    "lottery": ["won", "prize", "winner", "lottery", "lucky draw"],
    "investment": ["invest", "profit", "return", "trading", "crypto"],
    "tech_support": ["virus", "hacked", "microsoft", "apple", "tech support"],
}


class EnhancedScamDetector:
    """
    Multi-factor scam detection system.

    Combines linguistic, behavioral, technical, context, and LLM analysis
    to produce accurate scam detection with low false positives.
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
        metadata: Optional[Dict] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict:
        """Comprehensive scam analysis using multi-factor detection."""
        if metadata is None:
            metadata = {}
        if conversation_history is None:
            conversation_history = []

        logger.info(f"Enhanced detection analyzing: {message[:50]}...")

        try:
            linguistic_result = self.linguistic_analyzer.analyze(message)
            behavioral_result = self.behavioral_analyzer.analyze(message, metadata)
            technical_result = self.technical_analyzer.analyze(message)
            context_result = self.context_analyzer.analyze(
                message, metadata, conversation_history
            )
            llm_result = await self.llm_detector.analyze(
                message, metadata, conversation_history
            )
        except Exception as e:
            logger.error(f"Error in scam analysis: {str(e)}")
            return self._get_fallback_result(message)

        final_result = self._combine_results(
            linguistic_result, behavioral_result,
            technical_result, context_result,
            llm_result, message
        )

        logger.info(
            f"Enhanced detection result: is_scam={final_result['is_scam']}, "
            f"confidence={final_result['confidence']:.2f}, "
            f"type={final_result['scam_type']}"
        )

        return final_result

    def _combine_results(
        self,
        linguistic: Dict, behavioral: Dict,
        technical: Dict, context: Dict,
        llm: Dict, message: str
    ) -> Dict:
        """Combine all analysis results into final decision."""
        factor_scores = {
            "linguistic": linguistic.get("overall_linguistic_score", 0.0),
            "behavioral": behavioral.get("overall_behavioral_score", 0.0),
            "technical": technical.get("overall_technical_score", 0.0),
            "context": context.get("overall_context_score", 0.0),
            "llm": self._calculate_llm_score(llm)
        }

        overall_score = sum(
            factor_scores[factor] * self.weights[factor]
            for factor in self.weights
        )

        is_scam = overall_score >= self.confidence_threshold

        # If LLM is very confident, trust it more
        llm_confidence = llm.get("confidence", 0.5)
        if llm_confidence >= self.llm_high_confidence:
            is_scam = llm.get("is_scam", is_scam)
            overall_score = llm_confidence if llm.get("is_scam") else (1 - llm_confidence)

        red_flags = self._collect_red_flags(
            linguistic, behavioral, technical, context, llm
        )
        legitimacy_signals = llm.get("legitimacy_signals", [])
        scam_type = self._determine_scam_type(message, llm, red_flags)
        urgency_level = self._determine_urgency(linguistic, behavioral)
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
            "key_indicators": red_flags[:5],
            "llm_analysis": llm.get("reasoning", "")
        }

    def _calculate_llm_score(self, llm: Dict) -> float:
        """Calculate LLM contribution to score."""
        if llm.get("is_scam") is None:
            return 0.5
        confidence = llm.get("confidence", 0.5)
        return confidence if llm.get("is_scam") else 1.0 - confidence

    def _collect_red_flags(
        self,
        linguistic: Dict, behavioral: Dict,
        technical: Dict, context: Dict,
        llm: Dict
    ) -> List[str]:
        """Collect all red flags from different analyzers."""
        red_flags = []
        threshold = DETECTION_CONFIG["red_flag_threshold"]

        # Linguistic red flags
        linguistic_checks = [
            ("urgency_score", "High urgency language detected"),
            ("threat_score", "Threatening language detected"),
            ("authority_score", "Authority impersonation detected"),
            ("manipulation_score", "Emotional manipulation detected"),
        ]
        for score_key, flag_text in linguistic_checks:
            if linguistic.get(score_key, 0) > threshold:
                red_flags.append(flag_text)

        # Behavioral red flags
        behavioral_checks = [
            ("information_request_score", 0.7, "Requests sensitive personal information"),
            ("payment_demand_score", 0.7, "Demands payment or money transfer"),
            ("secrecy_score", 0.5, "Requests secrecy or confidentiality"),
            ("time_pressure_score", threshold, "Creates artificial time pressure"),
        ]
        for score_key, check_threshold, flag_text in behavioral_checks:
            if behavioral.get(score_key, 0) > check_threshold:
                red_flags.append(flag_text)

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

        # Add LLM-identified red flags (deduplicated)
        for flag in llm.get("red_flags", []):
            if flag not in red_flags:
                red_flags.append(flag)

        return list(dict.fromkeys(red_flags))

    def _determine_scam_type(
        self, message: str, llm: Dict, red_flags: List[str]
    ) -> str:
        """Determine type of scam."""
        # Trust LLM's classification if available
        llm_type = llm.get("scam_type", "")
        if llm_type and llm_type not in ("unknown", "legitimate"):
            return llm_type

        # Fallback: infer from keywords
        message_lower = message.lower()
        for scam_type, keywords in SCAM_TYPE_KEYWORDS.items():
            if any(word in message_lower for word in keywords):
                return scam_type

        return "other"

    def _determine_urgency(self, linguistic: Dict, behavioral: Dict) -> str:
        """Determine urgency level."""
        combined = (
            linguistic.get("urgency_score", 0)
            + linguistic.get("threat_score", 0)
            + behavioral.get("time_pressure_score", 0)
        ) / 3

        if combined >= 0.7:
            return "critical"
        if combined >= 0.5:
            return "high"
        if combined >= 0.3:
            return "medium"
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
            reasoning = f"Classified as SCAM with {confidence * 100:.0f}% confidence. "

            top_factors = sorted(
                factor_scores.items(), key=lambda x: x[1], reverse=True
            )[:2]
            factor_names = [
                f"{name} analysis" for name, score in top_factors if score > 0.5
            ]
            if factor_names:
                reasoning += f"Primary indicators: {', '.join(factor_names)}. "

            if red_flags:
                reasoning += f"Red flags: {', '.join(red_flags[:3])}."
        else:
            reasoning = f"Classified as LEGITIMATE with {(1 - confidence) * 100:.0f}% confidence. "
            if legitimacy_signals:
                reasoning += f"Legitimacy indicators: {', '.join(legitimacy_signals[:2])}."
            else:
                reasoning += "No significant scam indicators detected."

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
