"""
Response Variation Engine for AI Honeypot.
Transforms AI-generated responses into human-like text with natural imperfections.
"""

import random
import re
from typing import Dict, List

from app.agents.enhanced_personas import ENHANCED_PERSONAS


class ResponseVariationEngine:
    """Adds human-like variation to AI-generated responses."""
    
    # AI patterns to remove
    AI_PATTERNS = [
        r"^(I understand|I see|I appreciate|I apologize|I'm sorry to hear)\.",
        r"^(Certainly|Definitely|Absolutely|Of course)\.",
        r"(That's quite|That's rather|That's very)\s",
        r"I'm (quite|rather|somewhat|particularly)\s",
        r"^(Thank you for|Thanks for) (sharing|providing|letting me know)",
        r"\. (How can I assist|What else can I|Is there anything)",
        r"(Please feel free to|Don't hesitate to|Feel free to)\s",
        r"^(However,|Nevertheless,|Furthermore,|Additionally,)",
        r"I would be happy to",
        r"I hope this helps",
    ]
    
    # Autocorrect fail patterns
    AUTOCORRECT_FAILS = {
        "luck": "duck",
        "shot": "short",
        "send": "sens",
        "what": "ehat",
        "link": "lunk",
        "bank": "bnak",
        "money": "moeny",
        "account": "accoutn"
    }
    
    def __init__(self):
        self.message_count = {}
    
    def humanize_response(
        self,
        base_response: str,
        persona_name: str,
        session_id: str,
        message_number: int
    ) -> str:
        """Transform AI response into human-like text."""
        
        # Track message count for variation
        if session_id not in self.message_count:
            self.message_count[session_id] = 0
        self.message_count[session_id] += 1
        
        response = base_response.strip()
        persona = ENHANCED_PERSONAS.get(persona_name, ENHANCED_PERSONAS["tech_naive_parent"])
        
        # Step 1: Remove AI-like phrases
        response = self._remove_ai_patterns(response)
        
        # Step 2: Apply persona-specific variations
        response = self._apply_persona_variations(response, persona)
        
        # Step 3: Add natural imperfections
        response = self._add_natural_imperfections(response, persona)
        
        # Step 4: Vary opening and closing
        response = self._vary_opening_closing(response, persona, message_number)
        
        # Step 5: Add emotional markers
        response = self._add_emotional_markers(response, persona, message_number)
        
        return response.strip()
    
    def _remove_ai_patterns(self, text: str) -> str:
        """Remove obvious AI assistant patterns."""
        for pattern in self.AI_PATTERNS:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)
        return text.strip()
    
    def _apply_persona_variations(self, text: str, persona: Dict) -> str:
        """Apply persona-specific language patterns."""
        persona_name = persona.get("name", "")
        
        if persona_name == "busy_professional":
            # Add abbreviations
            replacements = [
                ("you ", "u "),
                ("are ", "r "),
                ("why ", "y "),
                ("please ", "pls "),
                ("thanks", "thx"),
                ("right now", "rn"),
                ("by the way", "btw"),
                ("to be honest", "tbh"),
                ("because", "bc"),
                ("okay", "ok"),
            ]
            for old, new in replacements:
                if random.random() < 0.6:  # 60% chance for each
                    text = text.replace(old, new)
                    text = text.replace(old.capitalize(), new)
        
        elif persona_name == "curious_student":
            # Add modern slang
            slang_replacements = {
                "really?": ["fr?", "seriously?", "no way", "wait fr?"],
                "suspicious": ["sus", "sketchy", "kinda sus"],
                "I don't know": ["idk", "not sure tbh", "idk..."],
                "okay": ["ok", "bet", "alr", "aight"],
                "I agree": ["bet", "ok bet", "yeah bet"],
                "interesting": ["lowkey interesting", "kinda cool"],
            }
            for old, options in slang_replacements.items():
                if old.lower() in text.lower():
                    text = re.sub(re.escape(old), random.choice(options), text, flags=re.IGNORECASE)
        
        elif persona_name == "elderly_confused":
            # Make more fragmented and uncertain
            if len(text.split()) > 12:
                words = text.split()
                mid = len(words) // 2
                text = " ".join(words[:mid]) + ". " + " ".join(words[mid:])
        
        return text
    
    def _add_natural_imperfections(self, text: str, persona: Dict) -> str:
        """Add realistic typos and imperfections."""
        typo_config = persona.get("typo_patterns", {})
        frequency = typo_config.get("frequency", 0.15)
        
        # Decide if this message should have imperfections
        if random.random() > frequency:
            return text
        
        typo_types = typo_config.get("types", [])
        if not typo_types:
            return text
        
        # Pick a random imperfection type
        typo_type = random.choice(typo_types)
        
        if "pattern" in typo_type:
            pattern = typo_type["pattern"]
            
            if pattern == "no_capitalization":
                text = text.lower()
            
            elif pattern in ["drop_capitalization", "lowercase_start"]:
                text = text[0].lower() + text[1:] if text else text
            
            elif pattern == "no_punctuation":
                text = text.replace(".", "").replace("!", "").replace("?", "")
            
            elif pattern == "all_caps_word":
                words = text.split()
                if len(words) > 2:
                    idx = random.randint(0, len(words) - 1)
                    words[idx] = words[idx].upper()
                    text = " ".join(words)
            
            elif pattern == "extra_space_before_punctuation":
                text = re.sub(r'([.!?])', r' \1', text)
            
            elif pattern == "abbreviate_you_to_u":
                text = text.replace("you", "u").replace("You", "u")
            
            elif pattern == "missing_apostrophe":
                text = text.replace("don't", "dont").replace("can't", "cant")
                text = text.replace("I'm", "im").replace("it's", "its")
            
            elif pattern == "autocorrect_fail":
                for orig, fail in self.AUTOCORRECT_FAILS.items():
                    if orig in text.lower() and random.random() < 0.3:
                        text = re.sub(re.escape(orig), fail, text, flags=re.IGNORECASE)
                        break
        
        elif "find" in typo_type and "replace" in typo_type:
            if random.random() < typo_type.get("chance", 0.5):
                text = text.replace(typo_type["find"], typo_type["replace"], 1)
        
        return text
    
    def _vary_opening_closing(
        self,
        text: str,
        persona: Dict,
        message_number: int
    ) -> str:
        """Vary opening and closing phrases."""
        opening_styles = persona.get("opening_styles", [""])
        closing_styles = persona.get("closing_styles", [""])
        
        # Opening: Less frequent in later messages
        opening_chance = 0.3 if message_number <= 2 else 0.15
        if random.random() < opening_chance:
            opening = random.choice(opening_styles)
            if opening:
                # Keep case based on persona
                if persona.get("name") == "curious_student":
                    opening = opening.lower()
                else:
                    opening = opening.capitalize() if opening[0].islower() else opening
                text = f"{opening} {text}"
        
        # Closing: Vary by persona
        closing_chance = 0.15
        if persona.get("name") == "elderly_confused":
            closing_chance = 0.25
        elif persona.get("name") == "busy_professional":
            closing_chance = 0.05
        
        if random.random() < closing_chance:
            closing = random.choice(closing_styles)
            if closing:
                text = f"{text}. {closing}"
        
        return text
    
    
    def _add_emotional_markers(
        self,
        text: str,
        persona: Dict,
        message_number: int
    ) -> str:
        """Add emotional punctuation and markers."""
        emotional_states = persona.get("emotional_states", [])
        if not emotional_states:
            return text
        
        # Select emotional state based on message number
        state_index = min(message_number // 3, len(emotional_states) - 1)
        current_state = emotional_states[state_index]
        
        # Add emotional punctuation based on content
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["worried", "scared", "concerned"]):
            if random.random() < 0.4 and not text.endswith("!") and not text.endswith("?"):
                text += "!"
        
        if "?" in text and random.random() < 0.3:
            text = text.replace("?", "??", 1)
        
        if persona.get("name") == "elderly_confused" and random.random() < 0.2:
            text = text.replace(".", "...")
        
        return text
    
    def get_fallback_response(
        self,
        persona_name: str,
        conversation_stage: str = "generic"
    ) -> str:
        """Get natural fallback response if LLM fails."""
        fallbacks = {
            "elderly_confused": [
                "I'm confused. Can you explain again?",
                "What do you mean?",
                "I don't understand",
                "My grandson usually helps me with these things",
                "Is this serious? What should I do"
            ],
            "busy_professional": [
                "wait what",
                "can u send that again",
                "sorry was in meeting what did u say",
                "quick summary pls",
                "not following"
            ],
            "curious_student": [
                "wait what fr?",
                "idk what u mean",
                "explain pls",
                "that sounds sus tbh",
                "confused rn"
            ],
            "tech_naive_parent": [
                "I don't understand. Is this safe?",
                "Can you explain more simply?",
                "Should I call the bank about this?",
                "I'm not sure what to do",
                "Is it okay to do this?"
            ],
            "desperate_job_seeker": [
                "Yes, I'm interested. What's the next step?",
                "Thank you. What information do you need?",
                "I'm ready to proceed. Please guide me.",
                "I appreciate this opportunity.",
                "What should I do next?"
            ]
        }
        
        responses = fallbacks.get(persona_name, ["I understand. What should I do?"])
        return random.choice(responses)
    
    def validate_human_likeness(self, response: str, persona_name: str) -> bool:
        """Validate that response doesn't contain AI patterns."""
        response_lower = response.lower()
        
        # Check for AI patterns
        ai_tells = [
            "i apologize",
            "i understand your concern",
            "i'm an ai",
            "i cannot",
            "however,",
            "nevertheless,",
            "furthermore,",
            "i would be happy to",
            "certainly!",
            "absolutely!",
        ]
        
        for tell in ai_tells:
            if tell in response_lower:
                return False
        
        # Persona-specific validation
        if persona_name == "curious_student":
            # Check if too formal
            if response[0:1].isupper() and "." in response and len(response.split()) > 10:
                if not any(slang in response_lower for slang in ["fr", "ngl", "tbh", "sus", "bet"]):
                    return False
        
        return True
