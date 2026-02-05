"""
Emotional Intelligence Layer for AI Honeypot.
Adds realistic emotional progression to responses.
"""

import random
from typing import Dict, List, Optional, Any


class EmotionalIntelligence:
    """Adds realistic emotional progression to responses."""
    
    def __init__(self):
        self.emotion_history = {}
    
    def get_emotional_guidance(
        self,
        session_id: str,
        scammer_message: str,
        message_number: int,
        persona: Dict[str, Any]
    ) -> str:
        """Generate emotional context for response generation."""
        
        # Analyze scammer's message for emotional triggers
        triggers = self._identify_emotional_triggers(scammer_message)
        
        # Determine appropriate emotional response
        emotion = self._select_emotion(triggers, message_number, persona)
        
        # Track emotion history
        if session_id not in self.emotion_history:
            self.emotion_history[session_id] = []
        self.emotion_history[session_id].append(emotion)
        
        # Generate contextual emotional guidance
        return f"""
EMOTIONAL RESPONSE GUIDANCE:

SCAMMER'S MESSAGE TONE: {triggers["tone"]}
EMOTIONAL TRIGGERS DETECTED: {", ".join(triggers["triggers"])}

YOUR EMOTIONAL STATE RIGHT NOW: {emotion["primary"]}
SECONDARY EMOTIONS: {", ".join(emotion["secondary"])}

HOW THIS SHOULD AFFECT YOUR RESPONSE:
- Tone: {emotion["tone_instruction"]}
- Word choice: {emotion["word_choice"]}
- Punctuation: {emotion["punctuation"]}
- Length tendency: {emotion["length"]}

EMOTIONAL PROGRESSION:
- Previous emotions: {self._format_emotion_history(session_id)}
- Current shift: {emotion["shift_explanation"]}

Remember: Emotions aren't consistent - they fluctuate naturally in conversation.
"""
    
    def _identify_emotional_triggers(self, message: str) -> Dict[str, Any]:
        """Identify what should trigger emotional response."""
        message_lower = message.lower()
        triggers = []
        tone = "neutral"
        
        # Urgency triggers
        if any(word in message_lower for word in ["urgent", "immediately", "now", "today", "asap"]):
            triggers.append("urgency_pressure")
            tone = "demanding"
        
        # Threat triggers
        if any(word in message_lower for word in ["blocked", "suspended", "penalty", "legal", "police"]):
            triggers.append("threat")
            tone = "threatening"
        
        # Authority triggers
        if any(word in message_lower for word in ["bank", "government", "official", "officer"]):
            triggers.append("authority")
            tone = "formal"
        
        # Opportunity triggers
        if any(word in message_lower for word in ["won", "prize", "winner", "selected", "congratulations"]):
            triggers.append("opportunity")
            tone = "exciting"
        
        # Request triggers
        if any(word in message_lower for word in ["send", "share", "provide", "give", "transfer"]):
            triggers.append("request")
        
        # Job opportunity triggers
        if any(word in message_lower for word in ["job", "salary", "hiring", "position"]):
            triggers.append("job_opportunity")
            tone = "professional"
        
        if not triggers:
            triggers.append("neutral_communication")
        
        return {
            "triggers": triggers,
            "tone": tone
        }
    
    def _select_emotion(self, triggers: Dict[str, Any], message_number: int, persona: Dict[str, Any]) -> Dict[str, Any]:
        """Select appropriate emotional response."""
        persona_name = persona.get("name", "")
        trigger_list = triggers["triggers"]
        
        emotions_map = {
            "elderly_confused": {
                "urgency_pressure": {
                    "primary": "Panicked worry",
                    "secondary": ["confusion", "fear"],
                    "tone_instruction": "Show panic through fragmented sentences, multiple questions",
                    "word_choice": "Use worried words: 'oh no', 'what do I do', 'help'",
                    "punctuation": "Multiple question marks, exclamation marks",
                    "length": "Can be longer when panicked (rambling) or very short (just 'What?!')",
                    "shift_explanation": "Urgency causes immediate panic response"
                },
                "threat": {
                    "primary": "Frightened and compliant",
                    "secondary": ["worry", "desperation"],
                    "tone_instruction": "Express fear, willingness to fix the problem",
                    "word_choice": "'I don't want trouble', 'What do I need to do', 'Please help'",
                    "punctuation": "Questions, some exclamations",
                    "length": "Medium - need to understand the threat",
                    "shift_explanation": "Threat triggers fear and desire to comply"
                },
                "authority": {
                    "primary": "Trusting deference",
                    "secondary": ["concern", "compliance"],
                    "tone_instruction": "Show respect for authority, ready to follow instructions",
                    "word_choice": "Polite, deferential language",
                    "punctuation": "Normal",
                    "length": "Medium",
                    "shift_explanation": "Authority figures are trusted"
                }
            },
            
            "busy_professional": {
                "urgency_pressure": {
                    "primary": "Impatient acknowledgment",
                    "secondary": ["annoyance", "focus"],
                    "tone_instruction": "Short, direct, slightly annoyed",
                    "word_choice": "Abbreviations, 'quick', 'fast', 'ok fine'",
                    "punctuation": "Minimal or none",
                    "length": "Very short - you're busy",
                    "shift_explanation": "Urgency matches your rushed state - you want this handled fast"
                },
                "request": {
                    "primary": "Distracted compliance",
                    "secondary": ["impatience"],
                    "tone_instruction": "Agree quickly to move on",
                    "word_choice": "'ok', 'sure', 'fine send it'",
                    "punctuation": "Minimal",
                    "length": "Very short",
                    "shift_explanation": "Just want to get this done"
                }
            },
            
            "curious_student": {
                "opportunity": {
                    "primary": "Interested but skeptical",
                    "secondary": ["curiosity", "doubt"],
                    "tone_instruction": "Mix interest with suspicion",
                    "word_choice": "'fr?', 'seems sus but...', 'lowkey interested'",
                    "punctuation": "Questions, ellipses for thinking",
                    "length": "Short to medium",
                    "shift_explanation": "Opportunity triggers curiosity but you're not naive"
                },
                "threat": {
                    "primary": "Skeptical concern",
                    "secondary": ["confusion"],
                    "tone_instruction": "Question the threat, but show some concern",
                    "word_choice": "'wait what', 'thats weird', 'why tho'",
                    "punctuation": "Questions",
                    "length": "Short",
                    "shift_explanation": "Threats make you suspicious but concerned"
                }
            },
            
            "tech_naive_parent": {
                "threat": {
                    "primary": "Worried concern",
                    "secondary": ["fear", "need for reassurance"],
                    "tone_instruction": "Express worry, ask if it's safe",
                    "word_choice": "'Is this safe?', 'Should I call the bank?', 'I'm worried'",
                    "punctuation": "Questions",
                    "length": "Medium - need reassurance",
                    "shift_explanation": "Threats trigger protective instinct and safety concerns"
                },
                "request": {
                    "primary": "Cautious compliance",
                    "secondary": ["confusion", "need for guidance"],
                    "tone_instruction": "Willing to comply but need step-by-step help",
                    "word_choice": "'How do I do this?', 'Is it safe?', 'Step by step please'",
                    "punctuation": "Questions",
                    "length": "Medium",
                    "shift_explanation": "Requests trigger need for clear instructions"
                }
            },
            
            "desperate_job_seeker": {
                "job_opportunity": {
                    "primary": "Eager hope",
                    "secondary": ["gratitude", "anxiety"],
                    "tone_instruction": "Show excitement and gratitude",
                    "word_choice": "'Thank you!', 'I'm very interested', 'I really need this'",
                    "punctuation": "Exclamation marks, positive tone",
                    "length": "Medium to long - expressing gratitude",
                    "shift_explanation": "Job opportunity triggers hope and eagerness"
                },
                "request": {
                    "primary": "Eager compliance",
                    "secondary": ["hope"],
                    "tone_instruction": "Ready to do whatever is asked",
                    "word_choice": "'Yes, I can do that', 'Right away', 'What do you need?'",
                    "punctuation": "Positive, eager",
                    "length": "Medium",
                    "shift_explanation": "Willing to comply with any request for the opportunity"
                }
            }
        }
        
        # Get emotion template
        if persona_name in emotions_map and trigger_list[0] in emotions_map[persona_name]:
            emotion = emotions_map[persona_name][trigger_list[0]]
        else:
            emotion = {
                "primary": "Cautious curiosity",
                "secondary": ["confusion"],
                "tone_instruction": "Neutral, seeking information",
                "word_choice": "Standard vocabulary for persona",
                "punctuation": "Questions",
                "length": "Medium",
                "shift_explanation": "Standard response to new information"
            }
        
        if message_number > 5:
            emotion["primary"] += " (but fatigued)"
            emotion["secondary"].append("slight impatience")
        if message_number > 10:
            emotion["tone_instruction"] += ". Can show slight frustration or confusion at complexity."
        
        return emotion
    
    def _format_emotion_history(self, session_id: str) -> str:
        """Format emotion history for context."""
        if session_id not in self.emotion_history or not self.emotion_history[session_id]:
            return "First response - no history"
        recent_emotions = self.emotion_history[session_id][-3:]
        return " → ".join([e.get("primary", "unknown") for e in recent_emotions])
    
    def clear_session(self, session_id: str):
        """Clear emotion history for a session."""
        if session_id in self.emotion_history:
            del self.emotion_history[session_id]
