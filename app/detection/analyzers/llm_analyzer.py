"""
Advanced LLM Detector for Enhanced Scam Detection.
Uses multi-step reasoning and factor analysis for sophisticated scam detection.
"""

import json
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class AdvancedLLMDetector:
    """Enhanced LLM-based scam detection with better prompting."""
    
    def __init__(self, llm_client):
        self.llm = llm_client
    
    async def analyze(
        self,
        message: str,
        metadata: Dict = None,
        conversation_history: List[Dict] = None
    ) -> Dict:
        """
        Advanced LLM-based scam detection.
        
        Uses multi-step reasoning and factor analysis.
        
        Returns:
            {
                "is_scam": bool,
                "confidence": float,
                "scam_type": str,
                "reasoning": str,
                "red_flags": [...],
                "legitimacy_signals": [...],
                "factors": {...}
            }
        """
        if metadata is None:
            metadata = {}
        if conversation_history is None:
            conversation_history = []
        
        # Build enhanced prompt
        prompt = self._build_enhanced_prompt(message, metadata, conversation_history)
        
        try:
            # Generate analysis
            response = await self.llm.generate_json(
                prompt=prompt,
                temperature=0.1,  # Low temperature for consistent analysis
            )
            
            # Parse response
            result = json.loads(response)
            
            # Validate and normalize
            result = self._validate_result(result)
            
            return result
            
        except Exception as e:
            logger.warning(f"LLM detection failed: {str(e)}")
            # If LLM fails, return uncertain result
            return {
                "is_scam": None,
                "confidence": 0.5,
                "scam_type": "unknown",
                "reasoning": "LLM analysis failed",
                "red_flags": [],
                "legitimacy_signals": [],
                "factors": {}
            }
    
    def _build_enhanced_prompt(
        self,
        message: str,
        metadata: Dict,
        history: List[Dict]
    ) -> str:
        """Build comprehensive analysis prompt."""
        
        # Context information
        channel = metadata.get('channel', 'Unknown')
        is_first_message = not history or len(history) == 0
        
        prompt = f"""You are an expert scam detection system. Analyze this message using multi-factor reasoning.

MESSAGE TO ANALYZE:
"{message}"

CONTEXT:
- Channel: {channel}
- First message: {is_first_message}
- Conversation history: {len(history) if history else 0} previous messages

ANALYSIS FRAMEWORK:
Evaluate the message across these dimensions:

1. LINGUISTIC PATTERNS:
   - Does it use urgency language? (urgent, immediately, now, today)
   - Does it contain threats? (blocked, suspended, legal action)
   - Does it claim authority? (bank, government, official)
   - Does it use emotional manipulation? (fear, greed, panic)

2. BEHAVIORAL RED FLAGS:
   - Requests personal information? (password, PIN, OTP, account details)
   - Demands payment or money transfer?
   - Creates artificial time pressure?
   - Asks for secrecy? (don't tell anyone, keep confidential)

3. LEGITIMACY INDICATORS (check for these POSITIVE signs):
   - Professional language and formatting?
   - Provides verifiable contact information?
   - Uses official channels and domains?
   - Matches expected communication patterns?
   - Contains legitimate business context?

4. TECHNICAL ANALYSIS:
   - Contains URLs? Are they suspicious?
   - Uses link shorteners to hide destination?
   - Has suspicious domain names or typosquatting?
   - Includes proper sender identification?

5. CONTEXT APPROPRIATENESS:
   - Is this communication expected/solicited?
   - Is timing appropriate for message type?
   - Does channel match message sensitivity?

CRITICAL DISTINCTION:
- LEGITIMATE messages may contain words like "urgent", "verify", "account" in appropriate business context
- SCAMS combine multiple red flags: urgency + threats + payment requests + poor grammar + suspicious links

RESPOND IN THIS EXACT JSON FORMAT:
{{
  "is_scam": true or false,
  "confidence": 0.0 to 1.0,
  "scam_type": "bank_fraud | upi_fraud | phishing | job_scam | lottery | romance | investment | tech_support | other | legitimate",
  "reasoning": "Brief explanation of decision (2-3 sentences)",
  "red_flags": ["list", "of", "red", "flags"],
  "legitimacy_signals": ["list", "of", "positive", "indicators"],
  "factors": {{
    "linguistic": 0.0 to 1.0,
    "behavioral": 0.0 to 1.0,
    "technical": 0.0 to 1.0,
    "legitimacy": 0.0 to 1.0
  }}
}}

EXAMPLES FOR REFERENCE:

LEGITIMATE MESSAGE:
"Your Amazon order #12345 has been dispatched. Track at amazon.in/track"
Analysis: Professional, expected communication, legitimate domain, no suspicious requests
Result: {{ "is_scam": false, "confidence": 0.95 }}

SCAM MESSAGE:
"URGENT! Your bank account will be blocked TODAY. Verify immediately by sending OTP to 9999999999"
Analysis: Urgency + threats + requests sensitive info (OTP) + suspicious phone number
Result: {{ "is_scam": true, "confidence": 0.95 }}

AMBIGUOUS MESSAGE:
"Please update your KYC details for account verification"
Analysis: Could be legitimate or scam, no context, no official sender
Result: {{ "is_scam": true, "confidence": 0.6 }} (cautious approach)

Now analyze the given message:"""
        
        return prompt
    
    def _validate_result(self, result: Dict) -> Dict:
        """Validate and normalize LLM result."""
        
        # Ensure required fields exist
        required_fields = ['is_scam', 'confidence', 'scam_type']
        for field in required_fields:
            if field not in result:
                result[field] = None
        
        # Normalize confidence to 0-1 range
        if result.get('confidence') is not None:
            try:
                result['confidence'] = max(0.0, min(1.0, float(result['confidence'])))
            except (ValueError, TypeError):
                result['confidence'] = 0.5
        else:
            result['confidence'] = 0.5
        
        # Ensure is_scam is boolean
        if result.get('is_scam') is not None:
            result['is_scam'] = bool(result['is_scam'])
        
        # Add defaults for optional fields
        if 'reasoning' not in result:
            result['reasoning'] = "No reasoning provided"
        
        if 'red_flags' not in result or not isinstance(result['red_flags'], list):
            result['red_flags'] = []
        
        if 'legitimacy_signals' not in result or not isinstance(result['legitimacy_signals'], list):
            result['legitimacy_signals'] = []
        
        if 'factors' not in result or not isinstance(result['factors'], dict):
            result['factors'] = {}
        
        return result
