"""
Behavioral Analyzer for Advanced Scam Detection.
Analyzes behavioral patterns including unsolicited contact, information requests,
payment demands, time pressure, and secrecy requests.
"""

import re
from typing import Dict


class BehavioralAnalyzer:
    """Analyze behavioral patterns in messages for scam indicators."""
    
    def __init__(self):
        # Information request patterns
        self.info_patterns = [
            r"(share|provide|send|give|enter) (your|the) (password|pin|cvv|otp|code)",
            r"(account|card|bank) (number|details|information)",
            r"confirm (your|the) (identity|details|information)",
            r"verify (by|your) (sending|sharing|providing)",
            r"(what is|tell me) your (password|pin|account)",
            r"verify (your|the) (account|whatsapp|profile|details|identity)"
        ]
        
        # Sensitive terms
        self.sensitive_terms = [
            'password', 'pin', 'cvv', 'otp', 'account number', 
            'card number', 'aadhaar', 'pan'
        ]
        
        # Payment request patterns - ENHANCED
        self.payment_patterns = [
            r"(send|transfer|pay|deposit|paying) (money|amount|payment|₹|rs\.?)",
            r"pay (the |a )?fee",
            r"(registration|processing|handling|service) (fee|charge|cost)",
            r"(send|pay|paying) ₹?\d+",
            r"transfer to (this |the )?(account|upi|number)",
            r"payment (of|for) ₹?\d+",
            r"claim by (paying|transferring|sending)"  # Added for lottery scams
        ]
        
        # Time pressure patterns
        self.time_patterns = [
            r"(within|in) (\d+ )?(hours?|minutes?|days?)",
            r"expires? (today|tonight|soon|in)",
            r"(last|final) (chance|opportunity|warning|day)",
            r"(act|respond|reply|do) (now|immediately|today|asap)",
            r"before (it's too late|midnight|closing|expiry)"
        ]
        
        # Secrecy request patterns
        self.secrecy_patterns = [
            r"don'?t (tell|share|inform|mention)",
            r"keep (this |it )?(secret|confidential|private|between us)",
            r"(only|just) (you|between|our)",
            r"don'?t (contact|call|visit) (bank|police|anyone)"
        ]
    
    def analyze(self, message: str, metadata: Dict = None) -> Dict[str, float]:
        """
        Analyze behavioral patterns in message.
        
        Returns:
            {
                "unsolicited_score": 0.0-1.0,
                "information_request_score": 0.0-1.0,
                "payment_demand_score": 0.0-1.0,
                "time_pressure_score": 0.0-1.0,
                "secrecy_score": 0.0-1.0,
                "overall_behavioral_score": 0.0-1.0
            }
        """
        if metadata is None:
            metadata = {}
            
        message_lower = message.lower()
        
        # Unsolicited contact (if no prior conversation)
        unsolicited_score = self._check_unsolicited(metadata)
        
        # Information requests
        info_request_score = self._check_info_requests(message_lower)
        
        # Payment demands
        payment_score = self._check_payment_demands(message_lower)
        
        # Time pressure
        time_pressure_score = self._check_time_pressure(message_lower)
        
        # Secrecy requests
        secrecy_score = self._check_secrecy(message_lower)
        
        overall = (
            unsolicited_score * 0.20 +
            info_request_score * 0.25 +
            payment_score * 0.30 +
            time_pressure_score * 0.15 +
            secrecy_score * 0.10
        )
        
        return {
            "unsolicited_score": unsolicited_score,
            "information_request_score": info_request_score,
            "payment_demand_score": payment_score,
            "time_pressure_score": time_pressure_score,
            "secrecy_score": secrecy_score,
            "overall_behavioral_score": overall
        }
    
    def _check_unsolicited(self, metadata: Dict) -> float:
        """Check if this is unsolicited contact."""
        # In honeypot context, first message is always unsolicited
        # Check if there's prior conversation context
        is_first_message = metadata.get("is_first_message", True)
        if is_first_message:
            return 0.3  # Moderate suspicion for first contact
        return 0.1
    
    def _check_info_requests(self, message: str) -> float:
        """Check for requests for personal information."""
        matches = 0
        for pattern in self.info_patterns:
            if re.search(pattern, message):
                matches += 1
        
        # Personal info requests are VERY suspicious
        if matches >= 2:
            return 1.0
        elif matches == 1:
            return 0.8
        else:
            # Check for any sensitive terms
            if any(term in message for term in self.sensitive_terms):
                return 0.5
            return 0.0
    
    def _check_payment_demands(self, message: str) -> float:
        """Check for payment or money transfer requests."""
        matches = 0
        for pattern in self.payment_patterns:
            if re.search(pattern, message):
                matches += 1
        
        # Payment requests in first message = very suspicious
        if matches >= 2:
            return 0.9
        elif matches == 1:
            return 0.7
        else:
            # Check for UPI IDs or bank account numbers
            if re.search(r'\d{10,}@\w+', message) or re.search(r'\d{9,18}', message):
                return 0.5
            return 0.0
    
    def _check_time_pressure(self, message: str) -> float:
        """Check for artificial time pressure."""
        matches = sum(1 for pattern in self.time_patterns if re.search(pattern, message))
        
        if matches >= 2:
            return 0.8
        elif matches == 1:
            return 0.5
        else:
            return 0.0
    
    def _check_secrecy(self, message: str) -> float:
        """Check for requests to keep things secret."""
        matches = sum(1 for pattern in self.secrecy_patterns if re.search(pattern, message))
        
        # Secrecy requests are RED FLAGS
        if matches >= 1:
            return 1.0
        return 0.0
