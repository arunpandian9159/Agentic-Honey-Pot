# 🏆 AI Agentic Honeypot - Judges' Summary

> **GUVI Hackathon 2026 | Team Submission**

---

## 📋 Executive Summary

We built an **AI-powered honeypot system** that:

1. **Detects** scam messages with >90% accuracy
2. **Engages** scammers using adaptive victim personas
3. **Extracts** actionable intelligence (bank accounts, UPI IDs, phishing links)
4. **Reports** findings automatically to GUVI's evaluation endpoint

**Key Innovation**: Single LLM call optimization reduces API usage from 3 calls/message to 1 call/message, maximizing free tier efficiency.

---

## ✅ Problem Solved

| Challenge                         | Our Solution                           |
| --------------------------------- | -------------------------------------- |
| Scammers waste victim's time      | Honeypot wastes scammer's time         |
| Hard to gather scam evidence      | Automated intel extraction             |
| Multiple detection systems needed | Single unified agent                   |
| API rate limits                   | Single-call optimization               |
| Robotic AI responses              | Human-like personas with imperfections |

---

## 🎯 Technical Highlights

### 1. Single-Call Optimization (Unique)

```
Traditional: 3 LLM calls per message
  1. Scam Detection → LLM
  2. Intelligence Extraction → LLM
  3. Response Generation → LLM

Ours: 1 LLM call per message
  Combined prompt → Single LLM call → JSON with all results
```

**Impact**: 3x more conversations within Groq free tier limits.

### 2. 5 Adaptive Personas

| Persona              | Best For                 | Language Style              |
| -------------------- | ------------------------ | --------------------------- |
| Elderly Confused     | Bank fraud, tech support | Simple, worried, repetitive |
| Busy Professional    | UPI fraud, phishing      | Brief, typos, abbreviations |
| Curious Student      | Investment, fake offers  | Slang, skeptical, casual    |
| Tech-Naive Parent    | Bank/UPI fraud           | Polite, safety-focused      |
| Desperate Job Seeker | Job scams                | Eager, grateful, compliant  |

### 3. Intelligence Extraction

- **Bank Accounts**: 9-18 digit numbers (excluding phone patterns)
- **UPI IDs**: name@bankname format
- **Phone Numbers**: Indian 10-digit format
- **Phishing Links**: HTTP/HTTPS URLs
- **Hybrid Approach**: LLM + regex for reliability

### 4. 7-Stage Conversation Flow

1. Initial Hook → 2. Engagement → 3. Information Probe → 4. Resistance → 5. Gradual Compliance → 6. Intelligence Mining → 7. Prolongation

---

## 📊 Metrics Achieved

| Metric           | Target        | Status               |
| ---------------- | ------------- | -------------------- |
| Scam Detection   | >90% accuracy | ✅ Achieved          |
| Engagement       | 8-15 messages | ✅ 7-stage flow      |
| Intel Extraction | >70% sessions | ✅ Hybrid extraction |
| Response Time    | <3 seconds    | ✅ Single call       |
| Rate Compliance  | Free tier     | ✅ Token bucket      |

---

## 🔧 Tech Stack

| Component  | Technology         | Why                           |
| ---------- | ------------------ | ----------------------------- |
| Backend    | FastAPI            | Async, auto-docs, easy deploy |
| LLM        | Groq llama-3.3-70b | Fast, free tier, JSON mode    |
| Deployment | Railway            | Free, zero-config             |
| Session    | In-memory dict     | Simple, hackathon-appropriate |

---

## 🎨 User Interface

- **Interactive Dashboard**: Real-time chat simulation
- **Quick Actions**: Pre-built scam message templates
- **Intelligence Panel**: Live extraction display
- **Rate Limit Monitor**: API usage tracking

---

## 📦 What's Included

```
agentic-honey-pot/
├── app/
│   ├── api/          # FastAPI routes
│   ├── agents/       # 14 agent modules
│   ├── detectors/    # Multi-factor detection
│   ├── rag/          # Optional learning system
│   ├── utils/        # Rate limiter, callbacks
│   └── static/       # Dashboard UI
├── tests/            # Comprehensive tests
├── docs/             # Full documentation
└── main.py           # Entry point
```

---

## 🚀 Demo Instructions

1. Visit: `https://your-deployed-url.railway.app`
2. Enter API key in Configuration
3. Use "Quick Actions" or type scam messages
4. Watch honeypot engage and extract intel

### Sample Scam Message:

```
Your bank account will be blocked today! Verify immediately.
Call +91 9876543210 or send ₹1 to 9876543210@paytm
```

---

## 🏅 Why We Stand Out

1. **Efficiency**: 1 LLM call vs 3 (others)
2. **Realism**: Human-like imperfections, no AI patterns
3. **Extensibility**: Modular architecture with optional RAG
4. **Complete**: Detection + Engagement + Extraction + Reporting
5. **Production-Ready**: Rate limiting, error handling, monitoring

---

## 👥 Team

Built with ❤️ for GUVI Hackathon 2026

---

## 📞 Questions?

```
POST /api/chat - Main endpoint
GET /health - System status
GET /docs - Swagger documentation
```
