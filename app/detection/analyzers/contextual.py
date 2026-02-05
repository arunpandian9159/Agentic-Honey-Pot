"""
Context Analyzer for Advanced Scam Detection.
Analyzes message context including expected vs unsolicited communication,
timing appropriateness, and channel appropriateness.
"""

from datetime import datetime
from typing import Dict, List


class ContextAnalyzer:
    """Analyze message context for scam indicators."""
    
    def __init__(self):
        # Keywords that are highly suspicious in unsolicited first messages
        self.urgent_first_message_keywords = [
            'urgent', 'blocked', 'suspended', 'deactivated', 'expired',
            'immediately', 'action required', 'verify now'
        ]
        
        # Sensitive terms that should not be requested via SMS/WhatsApp
        self.sensitive_channel_terms = [
            'password', 'pin', 'cvv', 'otp', 'account number',
            'card number', 'aadhaar', 'pan number'
        ]
    
    def analyze(
        self,
        message: str,
        metadata: Dict = None,
        conversation_history: List[Dict] = None
    ) -> Dict[str, float]:
        """
        Analyze contextual factors.
        
        Returns:
            {
                "expected_communication_score": 0.0-1.0,
                "timing_score": 0.0-1.0,
                "channel_score": 0.0-1.0,
                "overall_context_score": 0.0-1.0
            }
        """
        if metadata is None:
            metadata = {}
        if conversation_history is None:
            conversation_history = []
        
        # Check if communication is expected
        expected_score = self._check_expected_communication(
            message, metadata, conversation_history
        )
        
        # Check timing appropriateness
        timing_score = self._check_timing(metadata)
        
        # Check channel appropriateness
        channel_score = self._check_channel(message, metadata)
        
        overall = (
            expected_score * 0.40 +
            timing_score * 0.30 +
            channel_score * 0.30
        )
        
        return {
            "expected_communication_score": expected_score,
            "timing_score": timing_score,
            "channel_score": channel_score,
            "overall_context_score": overall
        }
    
    def _check_expected_communication(
        self,
        message: str,
        metadata: Dict,
        history: List[Dict]
    ) -> float:
        """
        Check if this communication is expected.
        
        In honeypot context, first message is always unexpected.
        """
        message_lower = message.lower()
        
        # For honeypot: first unsolicited message is suspicious
        if not history or len(history) == 0:
            # Unsolicited messages about urgent issues = very suspicious
            if any(word in message_lower for word in self.urgent_first_message_keywords):
                return 0.8
            return 0.4  # Moderate suspicion
        
        # If in ongoing conversation, check context
        msg_count = len(history)
        
        # Early in conversation with urgency = suspicious
        if msg_count <= 2:
            if any(word in message_lower for word in self.urgent_first_message_keywords):
                return 0.6
            return 0.3
        
        # Later in conversation = less suspicious
        return 0.2
    
    def _check_timing(self, metadata: Dict) -> float:
        """Check if timing is appropriate."""
        # Use provided timestamp or current time
        timestamp = metadata.get("timestamp")
        
        if timestamp:
            try:
                # Assume timestamp is epoch milliseconds
                dt = datetime.fromtimestamp(timestamp / 1000)
                hour = dt.hour
            except Exception:
                hour = datetime.now().hour
        else:
            hour = datetime.now().hour
        
        # Late night messages (11 PM - 6 AM) are more suspicious
        if hour >= 23 or hour <= 6:
            return 0.6
        
        # Business hours = less suspicious
        if 9 <= hour <= 18:
            return 0.1
        
        # Evening = moderate
        return 0.3
    
    def _check_channel(self, message: str, metadata: Dict) -> float:
        """Check if channel is appropriate for message type."""
        channel = metadata.get('channel', 'Unknown').lower()
        message_lower = message.lower()
        
        # Banks don't ask for sensitive info via SMS/WhatsApp
        if channel in ['sms', 'whatsapp', 'telegram']:
            if any(term in message_lower for term in self.sensitive_channel_terms):
                return 0.9  # Very suspicious
        
        # Legitimate services use official channels
        if 'official' in message_lower or 'verified' in message_lower:
            if channel in ['sms', 'whatsapp']:
                return 0.5  # Claiming to be official but via SMS
        
        # Financial requests via informal channels
        if channel in ['sms', 'whatsapp', 'telegram']:
            financial_terms = ['transfer', 'pay', 'send money', 'upi', 'bank']
            if any(term in message_lower for term in financial_terms):
                return 0.6
        
        return 0.2  # Default moderate suspicion
