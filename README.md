# AI Honeypot API

An AI-powered honeypot system that autonomously detects scam messages, engages scammers with convincing human-like personas, and extracts actionable intelligence (bank accounts, UPI IDs, phishing links).

## Features

- **Scam Detection**: Uses LLM analysis with keyword-based fallback for reliable detection
- **Adaptive Personas**: 5 victim personas that adapt based on scam type and urgency
- **Guided Intelligence Extraction**: Extract bank accounts, UPI IDs, and phishing links using strategic tactics
- **Optimized Single-Call Agent**: Combined detection, extraction, and response in one LLM call for 3x performance
- **Conversation Management**: 7-stage conversation flow for maximum engagement
- **GUVI Callback**: Automatic reporting to evaluation endpoint

## Tech Stack

- **Backend**: FastAPI (async, auto-docs)
- **LLM**: Groq (llama-3.3-70b-versatile)
- **Deployment**: Railway
- **Session Storage**: In-memory (suitable for hackathon)

## What Makes My Honeypot Unique

After implementing Phase 2, you'll have:

### Human-Like Responses

- Not robotic or repetitive
- Natural variation and imperfections
- Emotional progression
- Persona-appropriate language

### Advanced Detection

- Same scam detection as others
- But better engagement keeps scammers talking longer
- More intelligence extracted per conversation

### Difficult to Detect

- Scammers can't tell it's a honeypot
- Passes as real victim
- No obvious AI patterns

### Production Ready

- Deployed on Railway
- Handles concurrent sessions
- Proper error handling
- GUVI callback integration

### Continuously Improving (with Phase 3)

- Learns from each conversation
- Gets better over time
- Analytics on what works
- Self-optimizing

## Quick Start

### 1. Clone and Setup

```bash
cd honeypot-api
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```
GROQ_API_KEY=your_groq_api_key_here
API_SECRET_KEY=your_secret_key_here
GUVI_CALLBACK_URL=https://hackathon.guvi.in/api/updateHoneyPotFinalResult
```

Generate a secure API key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Run Locally

```bash
python main.py
# or
uvicorn main:app --reload --port 8000
```

### 4. Test the API

Health check:

```bash
curl http://localhost:8000/health
```

Chat endpoint:

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test-001",
    "message": {
      "sender": "scammer",
      "text": "Your bank account will be blocked. Verify immediately.",
      "timestamp": 1234567890000
    },
    "conversationHistory": [],
    "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
  }'
```

## API Endpoints

| Endpoint    | Method | Description           |
| ----------- | ------ | --------------------- |
| `/`         | GET    | API information       |
| `/health`   | GET    | Health check          |
| `/metrics`  | GET    | Service metrics       |
| `/api/chat` | POST   | Main chat endpoint    |
| `/docs`     | GET    | Swagger documentation |

## Deployment to Railway

1. Install Railway CLI:

```bash
npm install -g railway
```

2. Login and deploy:

```bash
railway login
railway init
railway up
```

3. Set environment variables:

```bash
railway variables set GROQ_API_KEY=your_key
railway variables set API_SECRET_KEY=your_secret
railway variables set GUVI_CALLBACK_URL=https://hackathon.guvi.in/api/updateHoneyPotFinalResult
railway variables set ENVIRONMENT=production
```

4. Get your public URL:

```bash
railway domain
```

## Testing

Run tests:

```bash
pytest tests/ -v
```

## Project Structure

```
honeypot-api/
├── main.py                 # FastAPI entry point
├── requirements.txt        # Dependencies
├── Procfile               # Railway config
├── app/
│   ├── api/
│   │   ├── routes.py      # API endpoints
│   │   └── validators.py  # Pydantic models
│   ├── core/
│   │   ├── config.py      # Settings
│   │   ├── session.py     # Session management
│   │   └── llm.py         # Groq client
│   ├── agents/
│   │   ├── detector.py    # Scam detection
│   │   ├── personas.py    # Victim personas
│   │   ├── conversation.py # Conversation flow
│   │   ├── extractor.py   # Intel extraction
│   │   ├── extraction_strategies.py # Guided extraction tactics
│   │   ├── optimized.py   # Single-call optimized agent
│   │   ├── response_variation.py # Humanization engine
│   │   └── enhanced_personas.py # Detailed persona traits
│   └── utils/
│       ├── logger.py      # Logging
│       └── callbacks.py   # GUVI callback
└── tests/
    ├── mock_data.py       # Test data
    ├── test_api.py        # API tests
    └── test_detector.py   # Detector tests
```

## Personas

| Persona              | Age   | Best For                 |
| -------------------- | ----- | ------------------------ |
| Elderly Confused     | 65-80 | Bank fraud, tech support |
| Busy Professional    | 30-45 | UPI fraud, phishing      |
| Curious Student      | 18-25 | Investment, fake offers  |
| Tech-Naive Parent    | 40-60 | Bank fraud, UPI fraud    |
| Desperate Job Seeker | 25-40 | Job scams, investment    |

## Success Metrics

- **Scam Detection**: >90% accuracy
- **Engagement**: 8-15 message exchanges
- **Intelligence**: >70% sessions yield intel
- **Response Time**: <3 seconds

## License

MIT License - Built for GUVI Hackathon 2026
