"""
Scammer Psychology Profiler for AI Honeypot.

Analyzes conversation history to build a real-time psychological profile 
of the scammer. The profile drives adaptive response generation:
  - Impatient scammer → shorter, confused responses (waste their time)
  - Sophisticated scammer → more realistic persona (avoid detection)
  - Frustrated scammer → strategic "almost compliance" (extract more info)
"""

import logging
import re
from typing import Dict, List

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Linguistic marker sets used for pattern-based scoring
# ---------------------------------------------------------------------------

AGGRESSION_MARKERS = [
    "immediately", "now", "urgent", "right now", "hurry",
    "legal action", "police", "arrest", "court", "jail",
    "freeze", "block", "suspend", "terminate", "cancel",
    "consequences", "penalty", "fine", "warning", "last chance",
    "don't waste", "stop wasting", "listen to me", "do as i say",
    "you will regret", "final notice", "no choice",
]

IMPATIENCE_MARKERS = [
    "why haven't you", "i already told you", "how many times",
    "are you stupid", "can't you understand", "hurry up",
    "i'm waiting", "still waiting", "do it now", "what's taking so long",
    "just do it", "quickly", "fast", "asap", "come on", "hello?", "??",
    "respond", "reply", "are you there",
]

SOPHISTICATION_MARKERS = [
    "protocol", "procedure", "verification", "compliance",
    "regulatory", "reserve bank", "rbi", "sebi", "government",
    "official", "authorized", "certified", "department",
    "reference number", "case id", "ticket number",
    "encrypted", "secure portal", "two-factor", "biometric",
]

EMOTIONAL_MANIPULATION_MARKERS = {
    "fear": [
        "lose everything", "all your money", "account hacked",
        "someone accessed", "unauthorized transaction", "stolen",
        "danger", "risk", "at stake", "compromised",
    ],
    "urgency": [
        "only today", "expires", "deadline", "limited time",
        "last chance", "within 24 hours", "closing soon",
        "running out", "window closing",
    ],
    "authority": [
        "bank manager", "officer", "senior executive", "government",
        "cyber cell", "fraud department", "investigation team",
        "reserve bank", "head office",
    ],
    "guilt": [
        "help me", "i trusted you", "cooperate", "don't you care",
        "your family", "think about", "for your safety",
        "we're trying to help", "protect you",
    ],
    "greed": [
        "guaranteed", "double your money", "100% return",
        "risk free", "selected", "winner", "congratulations",
        "lucky", "exclusive offer", "million", "lakh", "crore",
    ],
}

# Maps profile characteristics to recommended response strategies
TACTIC_RECOMMENDATIONS = {
    "high_aggression_low_patience": "show_more_confusion",
    "high_sophistication": "more_realistic_persona",
    "high_manipulation": "strategic_almost_compliance",
    "frustrated": "dangle_compliance",
    "default": "maintain_engagement",
}


class ScammerProfiler:
    """
    Builds a psychological profile of the scammer from conversation history.
    
    The profile is consumed by the LLM prompt builder to dynamically adapt
    the honeypot's response strategy.
    """

    def analyze(self, conversation_history: List[Dict]) -> Dict:
        """
        Analyze full conversation history and return a psychological profile.

        Args:
            conversation_history: List of message dicts with 'sender' and 'text'.

        Returns:
            Dict with scores and recommended tactics.
        """
        scammer_messages = [
            m.get("text", "")
            for m in conversation_history
            if m.get("sender", "").lower() == "scammer"
        ]

        if not scammer_messages:
            return self._default_profile()

        all_text = " ".join(scammer_messages).lower()
        msg_count = len(scammer_messages)

        aggression = self._score_aggression(scammer_messages, all_text)
        patience = self._score_patience(scammer_messages, all_text, msg_count)
        sophistication = self._score_sophistication(all_text)
        manipulation = self._score_emotional_manipulation(all_text)
        weaknesses = self._predict_weaknesses(aggression, patience, sophistication, manipulation)
        tactic = self._recommend_tactic(aggression, patience, sophistication, manipulation)

        profile = {
            "aggression_level": round(aggression, 2),
            "patience_score": round(patience, 2),
            "sophistication": round(sophistication, 2),
            "emotional_manipulation": round(manipulation, 2),
            "dominant_manipulation_type": self._dominant_manipulation_type(all_text),
            "predicted_weaknesses": weaknesses,
            "recommended_tactic": tactic,
            "message_count_analyzed": msg_count,
        }

        logger.info(
            f"Profile: aggr={profile['aggression_level']} pat={profile['patience_score']} "
            f"soph={profile['sophistication']} manip={profile['emotional_manipulation']} → {tactic}"
        )
        return profile

    # ------------------------------------------------------------------
    # Scoring functions
    # ------------------------------------------------------------------

    def _score_aggression(self, messages: List[str], all_text: str) -> float:
        """Score aggression 0.0-1.0 based on threatening language."""
        hits = sum(1 for marker in AGGRESSION_MARKERS if marker in all_text)
        # Check for ALL CAPS words (shouting)
        caps_words = sum(
            1 for word in all_text.split()
            if word.isupper() and len(word) > 2
        )
        # Exclamation marks = aggressive tone
        exclamations = all_text.count("!")

        raw = (hits * 0.08) + (caps_words * 0.03) + (exclamations * 0.04)
        return min(raw, 1.0)

    def _score_patience(
        self, messages: List[str], all_text: str, msg_count: int
    ) -> float:
        """
        Score patience 0.0-1.0 (high = patient).
        Decreases when scammer shows signs of frustration.
        """
        impatience_hits = sum(1 for m in IMPATIENCE_MARKERS if m in all_text)

        # Repeated messages = impatient
        repeated = 0
        if len(messages) >= 3:
            recent = [m.lower().strip() for m in messages[-4:]]
            for i in range(len(recent) - 1):
                overlap = set(recent[i].split()) & set(recent[i + 1].split())
                if len(overlap) > max(len(recent[i].split()) * 0.6, 3):
                    repeated += 1

        # Increasing message length over time = still patient
        # Decreasing = losing patience
        length_trend = 0.0
        if len(messages) >= 3:
            early_avg = sum(len(m) for m in messages[:2]) / 2
            late_avg = sum(len(m) for m in messages[-2:]) / 2
            if early_avg > 0:
                ratio = late_avg / early_avg
                length_trend = 0.1 if ratio > 1.2 else (-0.1 if ratio < 0.6 else 0)

        raw_impatience = (impatience_hits * 0.1) + (repeated * 0.15) - length_trend
        patience = max(0.0, 1.0 - raw_impatience)
        return min(patience, 1.0)

    def _score_sophistication(self, all_text: str) -> float:
        """Score sophistication 0.0-1.0 based on technical vocabulary."""
        hits = sum(1 for m in SOPHISTICATION_MARKERS if m in all_text)

        # Check for structured patterns (reference numbers, formatted IDs)
        has_ref_numbers = bool(re.search(r'(ref|case|ticket|id)[:\s#-]*\w{4,}', all_text))
        has_formal_language = bool(re.search(
            r'(dear\s+(sir|madam|customer)|we\s+regret\s+to\s+inform|'
            r'as\s+per\s+(our|the)\s+records|kindly\s+note)', all_text
        ))

        raw = (hits * 0.07) + (0.15 if has_ref_numbers else 0) + (0.15 if has_formal_language else 0)
        return min(raw, 1.0)

    def _score_emotional_manipulation(self, all_text: str) -> float:
        """Score emotional manipulation 0.0-1.0 across all manipulation types."""
        total_hits = 0
        for _category, markers in EMOTIONAL_MANIPULATION_MARKERS.items():
            total_hits += sum(1 for m in markers if m in all_text)

        raw = total_hits * 0.06
        return min(raw, 1.0)

    def _dominant_manipulation_type(self, all_text: str) -> str:
        """Identify the most used manipulation category."""
        best_category = "none"
        best_score = 0
        for category, markers in EMOTIONAL_MANIPULATION_MARKERS.items():
            hits = sum(1 for m in markers if m in all_text)
            if hits > best_score:
                best_score = hits
                best_category = category
        return best_category

    # ------------------------------------------------------------------
    # Tactical recommendations
    # ------------------------------------------------------------------

    def _predict_weaknesses(
        self, aggression: float, patience: float,
        sophistication: float, manipulation: float
    ) -> List[str]:
        """Predict exploitable psychological weaknesses."""
        weaknesses = []
        if patience < 0.4:
            weaknesses.append("frustration")
        if aggression > 0.6:
            weaknesses.append("anger_management")
        if sophistication < 0.3:
            weaknesses.append("low_adaptability")
        if manipulation > 0.6:
            weaknesses.append("over_reliance_on_scripts")
        if patience < 0.3 and aggression > 0.5:
            weaknesses.append("time_pressure")
        if sophistication > 0.6:
            weaknesses.append("overconfidence")
        return weaknesses or ["generic_engagement"]

    def _recommend_tactic(
        self, aggression: float, patience: float,
        sophistication: float, manipulation: float
    ) -> str:
        """Recommend optimal response strategy based on profile."""
        if patience < 0.4 and aggression > 0.5:
            return TACTIC_RECOMMENDATIONS["high_aggression_low_patience"]
        if sophistication > 0.6:
            return TACTIC_RECOMMENDATIONS["high_sophistication"]
        if manipulation > 0.6:
            return TACTIC_RECOMMENDATIONS["high_manipulation"]
        if patience < 0.4:
            return TACTIC_RECOMMENDATIONS["frustrated"]
        return TACTIC_RECOMMENDATIONS["default"]

    def _default_profile(self) -> Dict:
        """Return baseline profile when no scammer messages exist."""
        return {
            "aggression_level": 0.3,
            "patience_score": 0.7,
            "sophistication": 0.3,
            "emotional_manipulation": 0.3,
            "dominant_manipulation_type": "none",
            "predicted_weaknesses": ["generic_engagement"],
            "recommended_tactic": "maintain_engagement",
            "message_count_analyzed": 0,
        }

    # ------------------------------------------------------------------
    # Prompt modifier for LLM integration
    # ------------------------------------------------------------------

    def get_prompt_modifier(self, profile: Dict) -> str:
        """
        Generate a concise prompt hint from the profile for LLM injection.
        
        Keeps it short (< 120 chars) to avoid wasting tokens.
        """
        tactic = profile.get("recommended_tactic", "maintain_engagement")
        patience = profile.get("patience_score", 0.7)
        aggression = profile.get("aggression_level", 0.3)
        manipulation_type = profile.get("dominant_manipulation_type", "none")

        hints = []

        if tactic == "show_more_confusion":
            hints.append("Scammer is impatient — act MORE confused, give shorter replies")
        elif tactic == "more_realistic_persona":
            hints.append("Scammer is sophisticated — be very realistic, avoid any AI patterns")
        elif tactic == "strategic_almost_compliance":
            hints.append("Scammer uses emotional tactics — almost comply, ask for THEIR details")
        elif tactic == "dangle_compliance":
            hints.append("Scammer is frustrated — show willingness but create small obstacles")
        else:
            hints.append("Keep scammer engaged naturally")

        if manipulation_type != "none" and manipulation_type != "generic_engagement":
            hints.append(f"Scammer uses {manipulation_type} tactics")

        return "PSYCHOLOGY: " + " | ".join(hints)
