# 🔧 Technical Documentation

> In-depth implementation details and design decisions for AI Agentic Honeypot

---

## Table of Contents

1. [Core Design Decisions](#core-design-decisions)
2. [Single-Call Optimization](#single-call-optimization)
3. [Persona System Implementation](#persona-system-implementation)
4. [Scam Detection Pipeline](#scam-detection-pipeline)
5. [Intelligence Extraction](#intelligence-extraction)
6. [Session Management](#session-management)
7. [Rate Limiting Implementation](#rate-limiting-implementation)
8. [Conversation Flow Engine](#conversation-flow-engine)
9. [Response Humanization](#response-humanization)
10. [Testing Strategy](#testing-strategy)
11. [Performance Considerations](#performance-considerations)
12. [Future Enhancements](#future-enhancements)

---

## Core Design Decisions

### Why FastAPI?

| Feature              | Benefit                |
| -------------------- | ---------------------- |
| Async support        | Non-blocking LLM calls |
| Pydantic integration | Built-in validation    |
| Auto-generated docs  | Easy testing           |
| Type hints           | Better IDE support     |
| Lightweight          | Fast cold starts       |

### Why Groq llama-3.3-70b-versatile?

| Feature        | Benefit                     |
| -------------- | --------------------------- |
| JSON mode      | Reliable structured output  |
| Free tier      | No cost for hackathon       |
| Fast inference | <2s response time           |
| Large context  | Handle conversation history |

### Why In-Memory Sessions?

| Pros                  | Cons                      |
| --------------------- | ------------------------- |
| Zero dependencies     | Lost on restart           |
| Very fast             | Single instance only      |
| Hackathon-appropriate | Not horizontally scalable |
| Simple implementation | Limited capacity          |

**Trade-off**: Acceptable for hackathon scope. Production would use Redis or PostgreSQL.

---

## Single-Call Optimization

### The Problem

Traditional honeypot architecture:

```
Message → Detection LLM → Extraction LLM → Response LLM → Reply
         (1 call)         (1 call)         (1 call)

Result: 3 LLM calls × 30 RPM = 10 messages/minute max
```

### Our Solution

Combined architecture:

```
Message → Combined LLM → Reply
         (1 call)

Result: 1 LLM call × 30 RPM = 30 messages/minute max
```

### Implementation

```python
# app/agents/optimized.py

prompt = f"""Analyze and respond. Output ONLY valid JSON.

MSG: "{scammer_message}"
HISTORY: {history_text}
PERSONA: {persona_prompt[:300]}
TACTIC: {stage_tactic}

JSON output:
{{"is_scam":true/false,"confidence":0.0-1.0,"scam_type":"...",
  "intel":{{"bank_accounts":[],"upi_ids":[],"phone_numbers":[],"links":[]}},
  "response":"victim reply 1-2 sentences"}}

SCAM SIGNS: urgency, threats, payment requests, OTP/KYC, prizes, job offers
EXTRACT: UPI IDs (x@bank), phones (10 digits), links (http), accounts (12+ digits)
RESPONSE RULES:
- Sound like a REAL person, not an AI
- Use persona-appropriate language and imperfections
- Vary response style from previous messages
- Keep scammer engaged, extract their payment details"""
```

### Fallback Strategy

If LLM fails, we have pure regex fallback:

```python
def _fallback_response(self, message: str, persona: str, msg_count: int) -> Dict:
    matches = [kw for kw in self.SCAM_KEYWORDS if kw in msg_lower]
    is_scam = len(matches) >= 2

    intel = {
        "bank_accounts": re.findall(r'\b\d{10,18}\b', message),
        "upi_ids": [u for u in re.findall(r'[\w\.\-]+@[\w]+', message)],
        "phone_numbers": re.findall(r'[6-9]\d{9}', message),
        "phishing_links": re.findall(r'https?://\S+', message),
    }
```

---

## Persona System Implementation

### Two-Tier Architecture

1. **Base Personas** (`app/agents/personas.py`)
   - Core characteristics
   - Scam type mappings
   - Basic system prompts

2. **Enhanced Personas** (`app/agents/enhanced_personas.py`)
   - Detailed variation patterns
   - Natural language quirks
   - Emotional state progressions

### Persona Selection Algorithm

```python
def _select_enhanced_persona(self, scam_type: str) -> str:
    persona_mapping = {
        "bank_fraud": ["elderly_confused", "tech_naive_parent"],
        "upi_fraud": ["elderly_confused", "tech_naive_parent", "busy_professional"],
        "phishing": ["elderly_confused", "curious_student", "tech_naive_parent"],
        "job_scam": ["desperate_job_seeker", "curious_student"],
        "lottery": ["elderly_confused", "curious_student"],
        "investment": ["busy_professional", "curious_student"],
        "tech_support": ["elderly_confused", "tech_naive_parent"],
    }
    candidates = persona_mapping.get(scam_type, ["tech_naive_parent"])
    return random.choice(candidates)
```

### Enhanced Persona Structure

```python
ENHANCED_PERSONAS = {
    "elderly_confused": {
        "name": "elderly_confused",
        "base_traits": {
            "age": "65-80",
            "tech_skill": "very_low",
            "trust_level": "high",
        },
        "opening_styles": ["", "oh dear", "oh my", "goodness", "oh no"],
        "closing_styles": ["", "please help", "I'm so confused"],
        "sentence_patterns": ["short", "questioning", "worried"],
        "emotional_states": ["panic", "confusion", "relief", "fear"],
        "quirks": [
            "mentions grandson who helps with tech",
            "asks if should call bank instead",
            "forgets things from 2 messages ago",
        ],
        "typo_patterns": {
            "missing_punctuation": 0.3,
            "extra_spaces": 0.2,
            "random_caps": 0.15,
        },
        "enhanced_system_prompt": """You are a 70-year-old person who struggles with technology..."""
    }
}
```

---

## Scam Detection Pipeline

### Multi-Factor Detection (Extended)

Located in `app/detectors/`:

1. **Linguistic Analyzer** - Urgency, threats, manipulation language
2. **Behavioral Analyzer** - Unsolicited contact, payment demands
3. **Technical Analyzer** - URL analysis, domain verification
4. **Context Analyzer** - Conversation patterns, entity persistence

### Primary Detection (LLM)

```python
# app/agents/detector.py

scam_indicators = """
- Urgency/threats: "account blocked", "immediate action", "legal action"
- Authority impersonation: "bank", "government", "police", "RBI"
- Payment requests: UPI IDs, bank accounts, "send money", "pay fees"
- Personal info requests: "verify", "share OTP", "confirm details"
- Links: suspicious URLs, shortened links, fake domains
- Too-good offers: "won prize", "free gift", "guaranteed returns"
"""
```

### Keyword-Based Fallback

```python
SCAM_KEYWORDS = [
    # Urgency
    "urgent", "immediately", "today", "blocked", "suspended",
    # Authority
    "sbi", "hdfc", "icici", "rbi", "bank", "customer care",
    # Financial
    "upi", "account", "transfer", "pay", "payment",
    # Personal info
    "verify", "kyc", "otp", "cvv", "pin", "password",
    # Red flags
    "won", "winner", "prize", "lottery", "selected", "shortlisted",
]
```

### Confidence Scoring

```python
# LLM-based: 0.0-1.0 from model output
# Fallback: matches × 0.20, capped at 0.95

# Detection threshold: 0.65
if result["confidence"] >= settings.SCAM_DETECTION_THRESHOLD:
    session["scam_detected"] = True
```

---

## Intelligence Extraction

### Hybrid Approach

1. **LLM Extraction** - Pattern understanding
2. **Regex Enhancement** - Never miss structured patterns

### Pattern Definitions

```python
# Indian phone numbers
phone_pattern = r'(?:\+91[\s\-]?)?[6-9]\d{9}'

# UPI IDs (excluding emails)
upi_pattern = r'[a-zA-Z0-9\.\-\_]+@[a-zA-Z]+'
email_domains = ["gmail", "yahoo", "hotmail", "outlook"]

# URLs
url_pattern = r'https?://[^\s<>"\']+|www\.[^\s<>"\']+

# Bank accounts (9-18 digits, not phone numbers)
account_pattern = r'\b\d{9,18}\b'
```

### Intelligence Scoring

```python
def calculate_score(self, intelligence: Dict) -> float:
    score = 0.0

    score += len(intelligence.get("bank_accounts", [])) * 3    # Highest value
    score += len(intelligence.get("upi_ids", [])) * 2         # High value
    score += len(intelligence.get("phishing_links", [])) * 2  # High value
    score += len(intelligence.get("phone_numbers", [])) * 1   # Medium value
    score += min(len(intelligence.get("suspicious_keywords", [])), 5) * 0.5

    # Variety bonus
    intel_types = sum([
        len(intelligence.get("bank_accounts", [])) > 0,
        len(intelligence.get("upi_ids", [])) > 0,
        len(intelligence.get("phishing_links", [])) > 0,
        len(intelligence.get("phone_numbers", [])) > 0
    ])

    if intel_types >= 3:
        score *= 1.2  # 20% bonus

    return round(score, 2)
```

---

## Session Management

### Session Structure

```python
def _create_empty_session(self, session_id: str) -> Dict:
    return {
        "session_id": session_id,
        "conversation_history": [],
        "scam_detected": False,
        "scam_confidence": 0.0,
        "scam_type": None,
        "persona": None,
        "intelligence": {
            "bank_accounts": [],
            "upi_ids": [],
            "phishing_links": [],
            "phone_numbers": [],
            "suspicious_keywords": []
        },
        "message_count": 0,
        "created_at": datetime.now(),
        "last_activity": datetime.now()
    }
```

### Auto-Cleanup

```python
def _cleanup_expired(self) -> None:
    now = datetime.now()
    expired = [
        sid for sid, session in self.sessions.items()
        if now - session["last_activity"] > self.session_timeout  # 30 min
    ]
    for sid in expired:
        del self.sessions[sid]
```

### Session Completion Triggers

```python
should_end = (
    session["message_count"] >= settings.MAX_MESSAGES_PER_SESSION or  # 15
    intel_score >= settings.INTELLIGENCE_SCORE_THRESHOLD              # 8.0
)
```

---

## Rate Limiting Implementation

### Token Bucket Algorithm

```python
@dataclass
class RateLimiter:
    config: RateLimitConfig  # RPM=30, RPD=1K, TPM=12K, TPD=100K
    _minute_requests: deque  # Sliding window
    _day_requests: deque
    _minute_tokens: deque    # (timestamp, count) tuples
    _day_tokens: deque
```

### Pre-Request Check

```python
async def wait_if_needed(self, estimated_tokens: int = 500) -> Optional[float]:
    wait_time = 0.0

    # Check RPM
    if len(self._minute_requests) >= config.requests_per_minute:
        oldest = self._minute_requests[0]
        wait_time = max(wait_time, 60 - (now - oldest) + 0.1)

    # Check TPM
    minute_tokens = sum(t[1] for t in self._minute_tokens)
    if minute_tokens + estimated_tokens > config.tokens_per_minute:
        wait_time = max(wait_time, 60 - (now - oldest) + 0.1)

    if wait_time > 0:
        await asyncio.sleep(wait_time)

    return wait_time
```

---

## Conversation Flow Engine

### 7-Stage Framework

```python
# app/agents/natural_flow.py

STAGE_GUIDANCE = {
    1: "Show concern, ask why",
    2: "Ask clarifying questions",
    3: "Build trust, show interest",
    4: "Request their verification first",
    5: "Show hesitation about actions",
    6: "Slowly comply, ask for payment details",
    7: "Report issues, prolong conversation"
}

def get_stage_guidance(msg_count: int) -> str:
    if msg_count <= 2:
        return STAGE_GUIDANCE[1]
    elif msg_count <= 4:
        return STAGE_GUIDANCE[2]
    # ... etc
```

### Context-Aware Hints

```python
# app/agents/context_aware.py

def get_concise_context(session: Dict, msg_count: int) -> str:
    hints = []

    if session.get("scam_detected"):
        hints.append(f"SCAM: {session.get('scam_type')}")

    intel = session.get("intelligence", {})
    if intel.get("upi_ids"):
        hints.append(f"Got UPI: {intel['upi_ids'][0]}")

    return " | ".join(hints) if hints else ""
```

---

## Response Humanization

### Variation Engine

```python
# app/agents/response_variation.py

class ResponseVariationEngine:
    def humanize_response(
        self,
        base_response: str,
        persona_name: str,
        session_id: str,
        message_number: int
    ) -> str:
        persona = ENHANCED_PERSONAS.get(persona_name)
        if not persona:
            return base_response

        response = base_response

        # Apply typo patterns
        if random.random() < persona["typo_patterns"]["missing_punctuation"]:
            response = self._remove_random_punctuation(response)

        # Vary opening
        if random.random() < 0.4:
            opening = random.choice(persona["opening_styles"])
            response = f"{opening} {response}".strip()

        # Add quirks
        if random.random() < 0.2:
            quirk = random.choice(persona["quirks"])
            response += f" {quirk}"

        return response
```

---

## Testing Strategy

### Test Categories

1. **Unit Tests** - Individual components
2. **Integration Tests** - API endpoints
3. **Mock Data Tests** - Synthetic scam messages

### Sample Test

```python
# tests/test_detector.py

@pytest.mark.asyncio
async def test_bank_fraud_detection():
    detector = ScamDetector(mock_llm_client)
    result = await detector.analyze(
        "Your bank account is blocked. Verify immediately!"
    )

    assert result["is_scam"] == True
    assert result["confidence"] >= 0.65
    assert result["scam_type"] in ["bank_fraud", "phishing"]
```

### Run Tests

```bash
pytest tests/ -v
pytest tests/test_api.py -v
pytest tests/test_enhanced_detection.py -v
```

---

## Performance Considerations

### Response Time Breakdown

| Stage               | Target  | Actual    |
| ------------------- | ------- | --------- |
| Request parsing     | <10ms   | ~5ms      |
| Session lookup      | <5ms    | ~1ms      |
| LLM call            | <2s     | ~1.5s     |
| Response processing | <50ms   | ~20ms     |
| **Total**           | **<3s** | **~1.6s** |

### Optimizations Applied

1. **Token efficiency**: Truncated persona prompts to 300 chars
2. **History limiting**: Only last 3 messages in context
3. **Reduced max_tokens**: 250 vs default 500
4. **JSON mode**: Faster parsing, no retries

---

## Future Enhancements

### Planned Features

1. **Scammer Psychology Profiling** - Analyze aggression, patience, sophistication
2. **Multi-Language Support** - Hindi, Tamil, Telugu scam detection
3. **Live Analytics Dashboard** - Real-time statistics
4. **RAG-Powered Learning** - Learn from successful conversations

### Architecture Ready

```
# Optional RAG integration point
if is_rag_enabled():
    from app.agents.rag_conversation_manager import RAGEnhancedConversationManager
    agent = RAGEnhancedConversationManager(groq_client, qdrant_client)
```
