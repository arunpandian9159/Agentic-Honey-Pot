# 📖 API Reference

> Complete API documentation for AI Agentic Honeypot

---

## Base URL

```
Production: https://your-app.railway.app
Development: http://localhost:8000
```

---

## Authentication

All authenticated endpoints require the `x-api-key` header:

```http
x-api-key: YOUR_API_SECRET_KEY
```

---

## Endpoints

### POST /api/chat

Main chat endpoint for scam message processing.

**Authentication**: Required

**Request Headers:**

```http
Content-Type: application/json
x-api-key: YOUR_API_SECRET_KEY
```

**Request Body:**

```json
{
  "sessionId": "string (required) - Unique session identifier",
  "message": {
    "sender": "string (required) - 'scammer' or 'user'",
    "text": "string (required) - Message content",
    "timestamp": "integer (required) - Unix timestamp in milliseconds"
  },
  "conversationHistory": [
    {
      "sender": "string",
      "text": "string",
      "timestamp": "integer"
    }
  ],
  "metadata": {
    "channel": "string (optional) - SMS | WhatsApp | Email | Chat",
    "language": "string (optional) - Default: English",
    "locale": "string (optional) - Default: IN"
  }
}
```

**Success Response (200):**

```json
{
  "status": "success",
  "reply": "string - Agent's response as victim persona"
}
```

**Error Response (401):**

```json
{
  "detail": "Invalid API key"
}
```

**Example:**

```bash
curl -X POST https://your-app.railway.app/api/chat \
  -H "x-api-key: your_secret_key" \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "session-001",
    "message": {
      "sender": "scammer",
      "text": "Your account will be blocked. Verify now.",
      "timestamp": 1706000000000
    },
    "conversationHistory": [],
    "metadata": {
      "channel": "SMS",
      "language": "English",
      "locale": "IN"
    }
  }'
```

---

### GET /health

Health check endpoint with rate limit status.

**Authentication**: Not required

**Response (200):**

```json
{
  "status": "healthy",
  "active_sessions": 5,
  "timestamp": "2026-02-04T12:00:00.000000",
  "groq_requests": 42
}
```

**Example:**

```bash
curl https://your-app.railway.app/health
```

---

### GET /metrics

Service metrics and statistics.

**Authentication**: Not required

**Response (200):**

```json
{
  "total_sessions": 100,
  "scams_detected": 85,
  "average_messages_per_session": 8.5,
  "total_intelligence_extracted": 142,
  "groq_requests": 200
}
```

**Example:**

```bash
curl https://your-app.railway.app/metrics
```

---

### GET /usage

Current rate limit usage statistics.

**Authentication**: Not required

**Response (200):**

```json
{
  "requests_this_minute": 5,
  "requests_today": 150,
  "tokens_this_minute": 2500,
  "tokens_today": 45000,
  "rpm_remaining": 25,
  "rpd_remaining": 850,
  "tpm_remaining": 9500,
  "tpd_remaining": 55000,
  "total_requests": 200,
  "total_tokens_all_time": 50000
}
```

---

### GET /info

API information and version.

**Authentication**: Not required

**Response (200):**

```json
{
  "name": "AI Honeypot API",
  "version": "1.1.0",
  "description": "AI-powered honeypot - optimized for Groq rate limits",
  "rate_limits": {
    "rpm": "5/30",
    "rpd": "150/1000",
    "tpm": "2500/12000"
  },
  "endpoints": {
    "chat": "POST /api/chat",
    "health": "GET /health",
    "metrics": "GET /metrics",
    "usage": "GET /usage",
    "info": "GET /info"
  }
}
```

---

### GET /

Serves the interactive dashboard.

**Authentication**: Not required

**Response**: HTML page

---

### GET /docs

Swagger UI documentation.

**Authentication**: Not required

**Response**: Interactive API documentation

---

### GET /redoc

ReDoc API documentation.

**Authentication**: Not required

**Response**: Alternative API documentation

---

## Data Models

### Message

```typescript
{
  sender: "scammer" | "user";
  text: string;
  timestamp: number; // Unix timestamp in milliseconds
}
```

### Metadata

```typescript
{
  channel?: "SMS" | "WhatsApp" | "Email" | "Chat"
  language?: string  // Default: "English"
  locale?: string    // Default: "IN"
}
```

### Intelligence (Internal)

```typescript
{
  bank_accounts: string[]
  upi_ids: string[]
  phishing_links: string[]
  phone_numbers: string[]
  suspicious_keywords: string[]
}
```

### Scam Types

```typescript
"bank_fraud" |
  "upi_fraud" |
  "phishing" |
  "job_scam" |
  "lottery" |
  "investment" |
  "tech_support" |
  "other";
```

---

## GUVI Callback Format

When a session completes, the system automatically sends to GUVI:

```json
{
  "sessionId": "string",
  "scamDetected": true,
  "totalMessagesExchanged": 15,
  "extractedIntelligence": {
    "bankAccounts": ["1234567890123"],
    "upiIds": ["scammer@paytm"],
    "phishingLinks": ["http://fake-bank.com"],
    "phoneNumbers": ["9876543210"],
    "suspiciousKeywords": ["urgent", "blocked", "verify"]
  },
  "agentNotes": "Scam type: bank_fraud. Persona: elderly_confused. Detection confidence: 0.92. Intelligence score: 8.50"
}
```

---

## Rate Limits

| Limit | Value   | Description         |
| ----- | ------- | ------------------- |
| RPM   | 30      | Requests per minute |
| RPD   | 1,000   | Requests per day    |
| TPM   | 12,000  | Tokens per minute   |
| TPD   | 100,000 | Tokens per day      |

The API automatically:

- Waits if limits would be exceeded
- Returns current usage via `/usage` endpoint
- Logs warnings when approaching limits

---

## Error Codes

| Code | Description                             |
| ---- | --------------------------------------- |
| 200  | Success                                 |
| 401  | Invalid or missing API key              |
| 422  | Validation error (invalid request body) |
| 500  | Internal server error                   |

---

## SDKs & Examples

### Python

```python
import httpx

async def send_message(session_id: str, message: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://your-app.railway.app/api/chat",
            headers={
                "x-api-key": "YOUR_KEY",
                "Content-Type": "application/json"
            },
            json={
                "sessionId": session_id,
                "message": {
                    "sender": "scammer",
                    "text": message,
                    "timestamp": int(time.time() * 1000)
                },
                "conversationHistory": [],
                "metadata": {"channel": "SMS"}
            }
        )
        return response.json()
```

### JavaScript

```javascript
async function sendMessage(sessionId, message) {
  const response = await fetch("https://your-app.railway.app/api/chat", {
    method: "POST",
    headers: {
      "x-api-key": "YOUR_KEY",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      sessionId,
      message: {
        sender: "scammer",
        text: message,
        timestamp: Date.now(),
      },
      conversationHistory: [],
      metadata: { channel: "SMS" },
    }),
  });
  return response.json();
}
```

### cURL

```bash
curl -X POST https://your-app.railway.app/api/chat \
  -H "x-api-key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"sessionId":"test","message":{"sender":"scammer","text":"Verify your account now!","timestamp":1706000000000},"conversationHistory":[]}'
```
