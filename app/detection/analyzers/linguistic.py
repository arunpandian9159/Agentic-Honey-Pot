"""
Linguistic Analyzer for Advanced Scam Detection.
Analyzes message language patterns including urgency, threats, authority claims,
emotional manipulation, and grammar quality.
"""

import re
from typing import Dict, List


class LinguisticAnalyzer:
    """Analyze message language patterns for scam indicators."""
    
    def __init__(self):
        # Urgency patterns (weighted by intensity)
        self.urgency_patterns = {
            "extreme": [
                r"immediately|asap|right now|urgent|emergency",
                r"today only|expires today|last chance",
                r"act now|don't wait|hurry"
            ],
            "high": [
                r"soon|quickly|fast|rapid|prompt",
                r"limited time|ending soon|almost over",
                r"24 hours|within.*hours"  # Added for investment scams
            ],
            "medium": [
                r"please|kindly|at your earliest|as soon as possible"
            ]
        }
        
        # Threat patterns
        self.threat_patterns = [
            r"will be (blocked|suspended|closed|terminated|cancelled)",
            r"lose access|lose your|account will",
            r"legal action|penalty|fine|consequences",
            r"report to (police|authorities|cybercrime)",
            r"your account (is|will be) (blocked|suspended|locked)"
        ]
        
        # Authority impersonation
        self.authority_patterns = [
            r"(official|authorized|verified|certified) (notification|message|alert)",
            r"from (your )?(bank|government|tax|police|court)",
            r"(RBI|SEBI|Income Tax|Cybercrime) (department|office|cell)",
            r"customer (support|service|care) (team|department)"
        ]
        
        # Manipulation patterns - ENHANCED for better detection
        self.manipulation_patterns = [
            r"congratulations|you('ve)? (won|win|are selected|qualified)",
            r"exclusive|special|limited|selected (customers?|users?)",
            r"free|bonus|reward|prize|gift",
            r"guaranteed|assured|confirmed|approved",
            r"double your (money|investment|returns?)",  # Added for investment scams
            r"200%|300%|500%|1000%.*returns?"  # Added for unrealistic returns
        ]
        
        # Common scam misspellings
        self.scam_misspellings = [
            'recieve', 'verfiy', 'acount', 'paymet', 'tranfer',
            'immedietly', 'importent', 'urgant', 'accout', 'verifiy'
        ]
    
    def analyze(self, message: str) -> Dict[str, float]:
        """
        Analyze linguistic patterns in message.
        
        Returns:
            {
                "urgency_score": 0.0-1.0,
                "threat_score": 0.0-1.0,
                "authority_score": 0.0-1.0,
                "manipulation_score": 0.0-1.0,
                "grammar_score": 0.0-1.0,
                "overall_linguistic_score": 0.0-1.0
            }
        """
        if not message or not message.strip():
            return {
                "urgency_score": 0.0,
                "threat_score": 0.0,
                "authority_score": 0.0,
                "manipulation_score": 0.0,
                "grammar_score": 0.0,
                "overall_linguistic_score": 0.0
            }
        
        message_lower = message.lower()
        
        # Score urgency
        urgency_score = self._score_urgency(message_lower, message)
        
        # Score threats
        threat_score = self._score_patterns(message_lower, self.threat_patterns)
        
        # Score authority claims
        authority_score = self._score_patterns(message_lower, self.authority_patterns)
        
        # Score manipulation
        manipulation_score = self._score_patterns(message_lower, self.manipulation_patterns)
        
        # Grammar quality (poor grammar = more suspicious)
        grammar_score = self._analyze_grammar(message)
        
        # Calculate overall linguistic score
        overall = (
            urgency_score * 0.25 +
            threat_score * 0.30 +
            authority_score * 0.20 +
            manipulation_score * 0.15 +
            grammar_score * 0.10
        )
        
        return {
            "urgency_score": urgency_score,
            "threat_score": threat_score,
            "authority_score": authority_score,
            "manipulation_score": manipulation_score,
            "grammar_score": grammar_score,
            "overall_linguistic_score": overall
        }
    
    def _score_urgency(self, message_lower: str, original: str) -> float:
        """Score urgency language (higher = more urgent)."""
        score = 0.0
        
        # Extreme urgency
        for pattern in self.urgency_patterns["extreme"]:
            if re.search(pattern, message_lower):
                score += 0.4
        
        # High urgency
        for pattern in self.urgency_patterns["high"]:
            if re.search(pattern, message_lower):
                score += 0.2
        
        # Medium urgency
        for pattern in self.urgency_patterns["medium"]:
            if re.search(pattern, message_lower):
                score += 0.1
        
        # Multiple exclamation marks
        exclamation_count = original.count('!')
        if exclamation_count >= 3:
            score += 0.3
        elif exclamation_count == 2:
            score += 0.15
        
        # ALL CAPS words
        words = original.split()
        caps_words = [w for w in words if w.isupper() and len(w) > 2]
        if len(caps_words) >= 3:
            score += 0.2
        
        return min(score, 1.0)
    
    def _score_patterns(self, message: str, patterns: List[str]) -> float:
        """Score presence of pattern matches."""
        matches = 0
        for pattern in patterns:
            if re.search(pattern, message):
                matches += 1
        
        # More matches = higher score
        if matches == 0:
            return 0.0
        elif matches == 1:
            return 0.4
        elif matches == 2:
            return 0.7
        else:
            return 1.0
    
    def _analyze_grammar(self, message: str) -> float:
        """
        Analyze grammar quality.
        Poor grammar = higher scam score.
        """
        issues = 0.0
        
        # Check for common grammar errors
        message_lower = message.lower()
        
        # Common misspellings
        for misspelling in self.scam_misspellings:
            if misspelling in message_lower:
                issues += 0.2
        
        # Excessive punctuation
        if message.count('!!!') >= 1:
            issues += 0.3
        
        # Missing spaces after punctuation
        if re.search(r'[.!?][A-Z]', message):
            issues += 0.2
        
        # All caps sentences
        sentences = re.split(r'[.!?]+', message)
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and sentence.isupper() and len(sentence) > 10:
                issues += 0.3
        
        # Excessive use of "dear"
        if message_lower.count('dear') >= 2:
            issues += 0.2
        
        return min(issues, 1.0)
