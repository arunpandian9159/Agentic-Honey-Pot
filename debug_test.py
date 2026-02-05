import asyncio
from unittest.mock import AsyncMock
from app.agents.enhanced_detector import EnhancedScamDetector

async def test():
    mock_llm = AsyncMock()
    mock_llm.generate_json.return_value = '{"is_scam": true, "confidence": 0.85, "scam_type": "bank_fraud", "reasoning": "Detected scam patterns", "red_flags": ["urgency"], "legitimacy_signals": [], "factors": {}}'
    
    detector = EnhancedScamDetector(mock_llm)
    result = await detector.analyze('URGENT! Your SBI account will be blocked. Send OTP to 9876543210 immediately!', {'channel': 'sms'})
    print('Result:', result)
    print('is_scam:', result['is_scam'])
    print('confidence:', result['confidence'])

if __name__ == "__main__":
    asyncio.run(test())