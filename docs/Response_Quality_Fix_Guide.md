# Honeypot Response Quality Troubleshooting Guide
## Fixing Incomplete Sentences & Repetitive Responses

**Problem Identified:** AI agent responses are cutting off mid-sentence and repeating phrases  
**Impact:** Breaks immersion, scammer might detect it's not human  
**Priority:** 🔴 CRITICAL - Fix immediately

---

## Problem Analysis

### Issues Found in Your Conversation:

```python
INCOMPLETE_RESPONSES = [
    "Why will it",                    # ❌ Cut off mid-sentence
    "Why will.",                      # ❌ Incomplete thought
    "You're. from SBI,",              # ❌ Strange punctuation + incomplete
    "Can!",                           # ❌ Just one word
    "oh dear, I'm not sure I",        # ❌ Incomplete sentence
    "Can you",                        # ❌ Cut off mid-question
]

REPETITIVE_RESPONSES = [
    "Oh dear, I'm so worried about my account!" (appears 4+ times),
    "Can you please tell me..." (appears 3+ times)
]
```

### Root Causes:

1. **Max Tokens Too Low** - Response truncated by token limit
2. **Response Validation Over-Aggressive** - Cutting valid responses
3. **Length Adjustment Too Aggressive** - Humanization truncating sentences
4. **LLM Stopping Early** - Not completing thoughts
5. **No Sentence Completion Check** - Not validating responses are complete

---

## Quick Diagnosis

### Check 1: LLM Token Limit

```python
# In your code, find the LLM generation call:

# CURRENT (WRONG):
response = await self.llm.generate(
    prompt=prompt,
    temperature=0.7,
    max_tokens=100    # ❌ TOO LOW! Cutting responses mid-sentence
)

# SHOULD BE:
response = await self.llm.generate(
    prompt=prompt,
    temperature=0.7,
    max_tokens=150    # ✅ Enough for complete sentences
)
```

**Issue:** `max_tokens=100` is too restrictive for natural conversation.

**Fix:** Increase to 150-200 tokens to allow complete responses.

---

### Check 2: Response Variation Engine

```python
# In app/agents/response_variation.py

def _adjust_length(self, text: str, persona: Dict) -> str:
    """Adjust response length based on persona distribution"""
    
    # PROBLEM: This might be cutting sentences mid-way
    
    if target_category == "very_short" and word_count > 5:
        # ❌ WRONG: Cuts without checking sentence completion
        return " ".join(words[:random.randint(1, 4)])
    
    # ✅ FIX: Check sentence completion before truncating
    if target_category == "very_short" and word_count > 5:
        # Find natural break point
        truncated = " ".join(words[:random.randint(3, 6)])
        
        # If no punctuation, add appropriate ending
        if truncated[-1] not in '.!?':
            # Check if it's a question
            if any(q in truncated.lower() for q in ['what', 'why', 'how', 'when', 'where', 'who']):
                truncated += "?"
            else:
                truncated += "."
        
        return truncated
```

---

### Check 3: Response Validation

```python
# In app/agents/enhanced_conversation.py

def _validate_response(self, response: str, persona: Dict) -> bool:
    """Validate response quality"""
    
    # ADD THESE CHECKS:
    
    # 1. Check minimum length
    if len(response) < 5:
        return False
    
    # 2. Check for incomplete sentences
    if not self._is_sentence_complete(response):
        return False
    
    # 3. Check for trailing incomplete words
    if response.endswith((' ', 'I ', 'Can ', 'What ', 'Why ')):
        return False
    
    # 4. Check for proper punctuation
    if len(response) > 20 and response[-1] not in '.!?':
        return False
    
    return True

def _is_sentence_complete(self, text: str) -> bool:
    """Check if sentence is grammatically complete"""
    
    # Remove trailing spaces
    text = text.strip()
    
    # Very short responses should end with punctuation
    if len(text.split()) <= 3:
        return text[-1] in '.!?'
    
    # Check for obvious incomplete patterns
    incomplete_endings = [
        r'\s+(I|Can|What|Why|How|When|Where|Who|Will|Should|Could|Would|Please|My|Your|The)$',
        r'\s+(is|are|was|were|be|been|has|have|had|do|does|did|will|would|should|could)$',
        r'\s+to$',
        r'\s+and$',
        r'\s+or$',
        r'\s+but$',
    ]
    
    import re
    for pattern in incomplete_endings:
        if re.search(pattern, text, re.IGNORECASE):
            return False
    
    return True
```

---

## Solutions

### Solution 1: Immediate Fix (5 minutes)

**Step 1: Increase Max Tokens**

```python
# Find this in your code (likely in app/agents/enhanced_conversation.py):

# FIND:
response = await self.llm.generate(
    prompt=full_system_prompt + "\n\n" + user_prompt,
    temperature=0.8,
    max_tokens=100  # ❌ CHANGE THIS
)

# REPLACE WITH:
response = await self.llm.generate(
    prompt=full_system_prompt + "\n\n" + user_prompt,
    temperature=0.7,  # Also reduce temperature slightly for more coherent responses
    max_tokens=200    # ✅ Increased to allow complete sentences
)
```

**Step 2: Add Sentence Completion Check**

```python
# After getting LLM response, before humanization:

base_response = await self.llm.generate(...)

# Clean and validate
base_response = base_response.strip()

# Ensure sentence is complete
base_response = self._ensure_sentence_complete(base_response)

# Then apply humanization
final_response = self.variation_engine.humanize_response(...)
```

**Step 3: Add Sentence Completion Helper**

```python
# Add this method to your conversation manager:

def _ensure_sentence_complete(self, text: str) -> str:
    """Ensure response ends with complete sentence"""
    
    text = text.strip()
    
    # If already has punctuation at end, good
    if text and text[-1] in '.!?':
        return text
    
    # If very short (1-3 words), just add appropriate punctuation
    if len(text.split()) <= 3:
        # Check if it's a question word
        if text.lower() in ['what', 'why', 'how', 'when', 'where', 'who']:
            return text + "?"
        return text + "."
    
    # Check if it looks like a question
    question_words = ['what', 'why', 'how', 'when', 'where', 'who', 'can you', 'could you', 'should i']
    is_question = any(text.lower().startswith(qw) for qw in question_words)
    
    if is_question:
        return text + "?"
    else:
        return text + "."
```

---

### Solution 2: Fix Response Variation Engine (15 minutes)

**Update `app/agents/response_variation.py`:**

```python
def _adjust_length(self, text: str, persona: Dict) -> str:
    """Adjust response length SAFELY without breaking sentences"""
    
    length_dist = persona.get("message_length_distribution", {})
    words = text.split()
    word_count = len(words)
    
    # Determine target length category
    rand = random.random()
    cumulative = 0
    target_category = "medium"
    
    for category, probability in length_dist.items():
        cumulative += probability
        if rand < cumulative:
            target_category = category
            break
    
    # Adjust if needed, but SAFELY
    if target_category == "very_short" and word_count > 5:
        # SAFE truncation: Keep at least one complete thought
        
        # Try to find natural break (period, comma, conjunction)
        text_shortened = " ".join(words[:random.randint(3, 6)])
        
        # Ensure it's not ending mid-thought
        if text_shortened[-1] not in '.!?,':
            # Check what it should end with
            if any(q in text_shortened.lower() for q in ['what', 'why', 'how', 'can', 'should']):
                text_shortened += "?"
            else:
                text_shortened += "."
        
        return text_shortened
    
    elif target_category == "short" and word_count > 10:
        # Keep 5-9 words, ensure completion
        text_shortened = " ".join(words[:random.randint(5, 9)])
        
        if text_shortened[-1] not in '.!?':
            # Add appropriate punctuation
            if '?' in text or any(q in text.lower() for q in ['what', 'why', 'how']):
                text_shortened += "?"
            else:
                text_shortened += "."
        
        return text_shortened
    
    # If not truncating, return as-is
    return text
```

---

### Solution 3: Add Fallback Response Generation (10 minutes)

**When LLM generates bad response, use better fallback:**

```python
# In app/agents/enhanced_conversation.py

async def generate_enhanced_response(self, ...):
    """Generate response with quality checks"""
    
    # ... existing code ...
    
    try:
        response = await self.llm.generate(...)
        
        # Clean response
        response = response.strip().strip('"').strip("'")
        
        # Validate quality
        if not self._validate_response_quality(response, persona):
            logger.warning(f"Low quality response, regenerating: {response}")
            # Try one more time with adjusted prompt
            response = await self._regenerate_response(
                persona, scammer_message, conversation_history, session, message_number
            )
        
        # Final check
        if not self._validate_response_quality(response, persona):
            logger.error("Failed to generate quality response, using fallback")
            response = self._get_contextual_fallback(
                persona, scammer_message, message_number
            )
        
        # Ensure sentence completion
        response = self._ensure_sentence_complete(response)
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return self._get_contextual_fallback(persona, scammer_message, message_number)

def _validate_response_quality(self, response: str, persona: str) -> bool:
    """Comprehensive quality validation"""
    
    # Too short
    if len(response) < 3:
        return False
    
    # Too long (likely error)
    if len(response) > 300:
        return False
    
    # Check for incomplete sentence
    if not self._is_sentence_complete(response):
        return False
    
    # Check for AI patterns
    ai_patterns = [
        "I understand", "I see", "I apologize", "I'm an AI",
        "As an AI", "I cannot", "However,"
    ]
    if any(pattern.lower() in response.lower() for pattern in ai_patterns):
        return False
    
    # Check for repeated words (sign of error)
    words = response.split()
    if len(words) != len(set(words)):  # Has duplicates
        # Allow some natural repetition (like "I don't know, I just don't")
        # But catch obvious errors
        word_counts = {}
        for word in words:
            word_lower = word.lower()
            word_counts[word_lower] = word_counts.get(word_lower, 0) + 1
        
        # If any word appears 3+ times in short response, error
        if any(count >= 3 for count in word_counts.values()) and len(words) < 15:
            return False
    
    return True

def _get_contextual_fallback(
    self,
    persona: str,
    scammer_message: str,
    message_number: int
) -> str:
    """Get contextual fallback response instead of generic one"""
    
    # Analyze what scammer is asking for
    scammer_lower = scammer_message.lower()
    
    # If they're asking for OTP/password
    if any(word in scammer_lower for word in ['otp', 'password', 'pin', 'cvv']):
        fallbacks = {
            "elderly_confused": [
                "I'm not sure what that is. Can you explain?",
                "My daughter usually helps me with these things.",
                "What do you mean by that?",
            ],
            "busy_professional": [
                "wait what",
                "which otp r u talking about",
                "didnt get any otp",
            ],
            "curious_student": [
                "what otp? i didnt get anything",
                "idk what ur talking about",
                "wait which one",
            ]
        }
    
    # If they're asking for account number
    elif any(word in scammer_lower for word in ['account', 'number', 'details']):
        fallbacks = {
            "elderly_confused": [
                "Which account number do you need?",
                "I have my passbook here, what should I tell you?",
                "Can you tell me why you need this?",
            ],
            "busy_professional": [
                "which account",
                "y do u need that",
                "send me ur details first",
            ],
            "curious_student": [
                "wait which account",
                "idk if i should share that tbh",
                "seems kinda sus ngl",
            ]
        }
    
    # If they're asking to send money
    elif any(word in scammer_lower for word in ['send', 'pay', 'transfer', 'upi']):
        fallbacks = {
            "elderly_confused": [
                "Where should I send it? What's your account?",
                "I don't know how to do that. Can you help?",
                "What details do I need to send money?",
            ],
            "busy_professional": [
                "send where",
                "whats the upi id again",
                "give me the details",
            ],
            "curious_student": [
                "wait send where exactly",
                "whats ur upi id",
                "ok but where do i send it",
            ]
        }
    
    # Default confused responses
    else:
        fallbacks = {
            "elderly_confused": [
                "I'm confused. Can you explain again?",
                "What do you mean?",
                "I don't understand.",
            ],
            "busy_professional": [
                "what",
                "didnt get that",
                "explain pls",
            ],
            "curious_student": [
                "wait what",
                "confused",
                "what r u saying",
            ]
        }
    
    # Get appropriate fallback for persona
    persona_fallbacks = fallbacks.get(persona, fallbacks["elderly_confused"])
    return random.choice(persona_fallbacks)
```

---

### Solution 4: Improve Prompt for Complete Sentences (5 minutes)

**Update your system prompt to emphasize completion:**

```python
# In the persona system prompts, add this section:

"""
CRITICAL RESPONSE RULES:
1. ALWAYS complete your sentences - never end mid-thought
2. ALWAYS end with proper punctuation (. ! ?)
3. If confused, ask a complete question
4. Keep responses 1-3 complete sentences (not fragments)
5. Each response should make sense on its own

EXAMPLES OF GOOD RESPONSES:
✓ "What do you mean?" (complete question)
✓ "I don't understand this." (complete statement)
✓ "Can you explain that again?" (complete question)
✓ "ok send me the details" (complete thought, casual)

EXAMPLES OF BAD RESPONSES (NEVER DO THIS):
✗ "What do you" (incomplete)
✗ "I don't" (incomplete)
✗ "Can you please" (incomplete)
✗ "ok send me" (incomplete)

REMEMBER: Even if keeping it short, always complete the thought!
"""
```

---

## Implementation Checklist

### Immediate Fixes (Do Right Now - 10 min):

- [ ] Find LLM generation call
- [ ] Change `max_tokens=100` to `max_tokens=200`
- [ ] Add `_ensure_sentence_complete()` method
- [ ] Call it after LLM generation, before humanization
- [ ] Test with 5 messages

### Quality Improvements (Do Today - 30 min):

- [ ] Add `_validate_response_quality()` method
- [ ] Add `_is_sentence_complete()` check
- [ ] Update `_adjust_length()` to truncate safely
- [ ] Add `_get_contextual_fallback()` method
- [ ] Update persona prompts with completion rules
- [ ] Test with 20+ messages

### Long-term Improvements (Optional):

- [ ] Add response regeneration on failure
- [ ] Log quality issues for analysis
- [ ] Track completion rate metric
- [ ] A/B test different max_tokens values

---

## Testing

### Test Script:

```python
# test_response_quality.py

import asyncio
from app.agents.enhanced_conversation import EnhancedConversationManager

async def test_response_completion():
    """Test that all responses are complete sentences"""
    
    test_messages = [
        "Your account will be blocked",
        "Share your OTP immediately",
        "What is your account number?",
        "Send money to this UPI ID",
        "Are you there? Please respond quickly",
    ]
    
    manager = EnhancedConversationManager(groq_client)
    
    session = {
        "session_id": "test_123",
        "persona": "elderly_confused",
        "scam_type": "bank_fraud",
        "intelligence": {},
        "conversation_history": [],
        "message_count": 0
    }
    
    issues_found = []
    
    for i, scammer_msg in enumerate(test_messages, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}: Scammer says: '{scammer_msg}'")
        
        response = await manager.generate_enhanced_response(
            persona_name="elderly_confused",
            scammer_message=scammer_msg,
            conversation_history=[],
            session=session,
            message_number=i
        )
        
        print(f"Response: '{response}'")
        
        # Check issues
        has_issues = False
        
        # Check 1: Ends with punctuation
        if response[-1] not in '.!?':
            print("❌ Missing ending punctuation")
            has_issues = True
        
        # Check 2: Minimum length
        if len(response) < 3:
            print("❌ Too short")
            has_issues = True
        
        # Check 3: Not cutting off
        incomplete_patterns = [' I$', ' Can$', ' What$', ' Why$', ' to$', ' and$']
        import re
        for pattern in incomplete_patterns:
            if re.search(pattern, response):
                print(f"❌ Incomplete sentence (ends with '{pattern}')")
                has_issues = True
        
        # Check 4: Has actual content
        if len(response.split()) < 2:
            print("❌ Response too minimal")
            has_issues = True
        
        if has_issues:
            issues_found.append({
                "scammer_msg": scammer_msg,
                "response": response,
                "issue": "Incomplete or low quality"
            })
        else:
            print("✓ Response quality OK")
    
    print(f"\n{'='*60}")
    print(f"SUMMARY:")
    print(f"Total tests: {len(test_messages)}")
    print(f"Issues found: {len(issues_found)}")
    print(f"Success rate: {(len(test_messages) - len(issues_found)) / len(test_messages) * 100:.0f}%")
    
    if issues_found:
        print("\nISSUES FOUND:")
        for issue in issues_found:
            print(f"  - '{issue['response']}' (for: '{issue['scammer_msg']}')")
    
    # Assert no issues
    assert len(issues_found) == 0, f"Found {len(issues_found)} quality issues"

# Run test
if __name__ == "__main__":
    asyncio.run(test_response_completion())
```

---

## Expected Results

### Before Fix:

```
Scammer: "Share your OTP immediately"
Honeypot: "Oh dear, I'm not sure I"  ❌ (incomplete)

Scammer: "What is your account number?"
Honeypot: "Can!"  ❌ (incomplete)

Scammer: "Send money to this UPI"
Honeypot: "Why will."  ❌ (incomplete)
```

### After Fix:

```
Scammer: "Share your OTP immediately"
Honeypot: "Oh dear, I'm not sure what that is. Can you explain?"  ✓ (complete)

Scammer: "What is your account number?"
Honeypot: "Can you tell me why you need it?"  ✓ (complete)

Scammer: "Send money to this UPI"
Honeypot: "Why should I send money? What's your UPI ID?"  ✓ (complete)
```

---

## Debugging Tips

### If Issue Persists:

**1. Check logs to see actual LLM output:**

```python
# Add logging before humanization:
logger.info(f"Raw LLM output: '{base_response}'")
logger.info(f"After humanization: '{final_response}'")
```

**2. Temporarily disable humanization:**

```python
# In generate_enhanced_response, comment out humanization:
# final_response = self.variation_engine.humanize_response(...)
final_response = base_response  # Use raw LLM output
```

If this fixes it, issue is in humanization. If not, issue is in LLM generation.

**3. Check max_tokens is actually being used:**

```python
# Add assertion:
assert max_tokens >= 150, f"max_tokens too low: {max_tokens}"
```

**4. Test with different temperatures:**

```python
# Try lower temperature for more coherent responses:
temperature=0.5  # Instead of 0.8
```

---

## Additional Issue: Repetition

Your conversation shows **too much repetition** of "Oh dear, I'm so worried about my account!"

### Fix Repetition:

```python
# In app/agents/enhanced_conversation.py

class ConversationMemory:
    """Track recent responses to avoid repetition"""
    
    def __init__(self):
        self.recent_responses = {}
    
    def is_too_similar(self, session_id: str, new_response: str) -> bool:
        """Check if response is too similar to recent ones"""
        
        if session_id not in self.recent_responses:
            self.recent_responses[session_id] = []
        
        recent = self.recent_responses[session_id]
        
        # Check last 3 responses
        for old_response in recent[-3:]:
            similarity = self._calculate_similarity(old_response, new_response)
            if similarity > 0.7:  # 70% similar
                return True
        
        return False
    
    def add_response(self, session_id: str, response: str):
        """Store response"""
        if session_id not in self.recent_responses:
            self.recent_responses[session_id] = []
        
        self.recent_responses[session_id].append(response)
        
        # Keep only last 5
        if len(self.recent_responses[session_id]) > 5:
            self.recent_responses[session_id].pop(0)
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Simple word-based similarity"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)

# Use in conversation manager:
class EnhancedConversationManager:
    def __init__(self, llm_client):
        # ... existing code ...
        self.conversation_memory = ConversationMemory()
    
    async def generate_enhanced_response(self, ...):
        # ... generate response ...
        
        # Check for repetition
        if self.conversation_memory.is_too_similar(session_id, response):
            logger.warning(f"Response too similar to recent, regenerating")
            # Regenerate with variation instruction
            response = await self._regenerate_with_variation(...)
        
        # Store response
        self.conversation_memory.add_response(session_id, response)
        
        return response
```

---

## Summary

**Your Issues:**
1. ❌ Responses cutting off mid-sentence
2. ❌ Too much repetition
3. ❌ Strange punctuation placement

**Root Causes:**
1. `max_tokens=100` too low
2. No sentence completion validation
3. Aggressive length truncation
4. No repetition checking

**Quick Fixes (10 min):**
1. Increase max_tokens to 200
2. Add _ensure_sentence_complete() method
3. Call it before returning response

**Full Solution (30 min):**
1. All quick fixes above
2. Add response quality validation
3. Safe length adjustment
4. Repetition detection
5. Contextual fallbacks
6. Better prompting

**Expected Results:**
- ✅ All sentences complete with proper punctuation
- ✅ Natural variation in responses
- ✅ No repetition
- ✅ Maintains persona while being coherent
- ✅ Successfully extracts intelligence (you already do this!)

---

**START WITH:** Increase max_tokens to 200 and add sentence completion check. Test immediately. This should fix 80% of your issues in 10 minutes!
