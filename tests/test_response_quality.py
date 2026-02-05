import pytest
from unittest.mock import AsyncMock
from app.agents.enhanced_conversation import EnhancedConversationManager


@pytest.mark.asyncio
async def test_responses_end_with_punctuation():
    mock_llm = AsyncMock()
    mock_llm.generate_json.return_value = (
        '{"is_scam": true, "confidence": 0.8, "scam_type": "bank_fraud", '
        '"intel": {"bank_accounts": [], "upi_ids": [], "phone_numbers": [], "links": []}, '
        '"response": "Oh dear, I dont understand"}'
    )
    manager = EnhancedConversationManager(mock_llm)
    session = {
        "session_id": "test_123",
        "persona": "elderly_confused",
        "scam_type": "bank_fraud",
        "intelligence": {},
        "conversation_history": [],
        "message_count": 0
    }
    result = await manager.process_message("Share your OTP immediately", session)
    resp = result["response"]
    assert resp[-1] in ".!?"
    assert len(resp.strip()) >= 3


@pytest.mark.asyncio
async def test_incomplete_patterns_rejected_and_fixed():
    mock_llm = AsyncMock()
    mock_llm.generate_json.return_value = (
        '{"is_scam": true, "confidence": 0.8, "scam_type": "bank_fraud", '
        '"intel": {"bank_accounts": [], "upi_ids": [], "phone_numbers": [], "links": []}, '
        '"response": "Can you"}'
    )
    mock_llm.generate.return_value = "Can you explain?"
    manager = EnhancedConversationManager(mock_llm)
    session = {"session_id": "s1", "persona": "busy_professional", "message_count": 0}
    result = await manager.process_message("What is your account number?", session)
    resp = result["response"]
    assert resp[-1] in ".!?"
    assert "Can you" != resp


@pytest.mark.asyncio
async def test_repetition_detection_variation():
    mock_llm = AsyncMock()
    mock_llm.generate_json.side_effect = [
        '{"is_scam": true, "confidence": 0.8, "scam_type": "bank_fraud", "intel": {"bank_accounts": [], "upi_ids": [], "phone_numbers": [], "links": []}, "response": "I dont understand"}',
        '{"is_scam": true, "confidence": 0.8, "scam_type": "bank_fraud", "intel": {"bank_accounts": [], "upi_ids": [], "phone_numbers": [], "links": []}, "response": "I dont understand"}',
    ]
    mock_llm.generate.side_effect = ["wait what", "ok send details"]
    manager = EnhancedConversationManager(mock_llm)
    session = {"session_id": "s2", "persona": "curious_student", "message_count": 0}
    r1 = await manager.process_message("Send money to this UPI", session)
    r2 = await manager.process_message("Send money now", session)
    assert r1["response"] != r2["response"]
