"""
Scammer ↔ Agent conversation test cases.

Each test simulates a 4-5 turn conversation for a specific persona × scam type
using offline functions only (no LLM / network calls).

Validates:
  - Scam detection (keyword-based)
  - Correct persona selection
  - Intelligence extraction (UPI IDs, phones, links, keywords)
  - Response generation (non-empty fallback)
  - Multi-turn stage progression
"""

import pytest

from app.agents.optimized import (
    quick_scam_type,
    _fallback_response,
    PERSONA_MAPPING,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_conversation(messages: list[str], persona: str) -> list[dict]:
    """Feed a list of scammer messages through _fallback_response and return results."""
    results = []
    for idx, msg in enumerate(messages, start=1):
        result = _fallback_response(msg, persona, msg_count=idx)
        results.append(result)
    return results


def _collect_intel(results: list[dict], key: str) -> list:
    """Collect all intel items of a specific key across all turns."""
    items = []
    for r in results:
        items.extend(r["intel"].get(key, []))
    return items


def _collect_keywords(results: list[dict]) -> set[str]:
    """Collect all suspicious keywords across all turns."""
    keywords = set()
    for r in results:
        keywords.update(r["intel"].get("suspicious_keywords", []))
    return keywords


# ---------------------------------------------------------------------------
# 1. Elderly Confused — Bank Fraud
# ---------------------------------------------------------------------------

class TestElderlyConfusedBankFraud:
    """Simulates an SBI bank-fraud scam against the elderly_confused persona."""

    PERSONA = "elderly_confused"
    SCAM_TYPE = "bank_fraud"
    MESSAGES = [
        "Dear customer, your SBI bank account has been blocked due to KYC verification. Call immediately to unblock.",
        "Please verify your identity by sharing the OTP sent to your registered mobile number.",
        "This is urgent! Your bank account will be permanently suspended today if you don't verify now.",
        "Send your OTP now or we will file a police complaint and take legal action against you.",
        "Your bank account number 1234567890123 will be deactivated. Share OTP to stop this.",
    ]

    def test_scam_type_detected(self):
        assert quick_scam_type(self.MESSAGES[0]) == self.SCAM_TYPE

    def test_persona_mapping(self):
        assert self.PERSONA in PERSONA_MAPPING[self.SCAM_TYPE]

    def test_first_message_detected_as_scam(self):
        result = _fallback_response(self.MESSAGES[0], self.PERSONA, msg_count=1)
        assert result["is_scam"] is True
        assert result["scam_type"] == self.SCAM_TYPE

    def test_multi_turn_responses_generated(self):
        results = _run_conversation(self.MESSAGES, self.PERSONA)
        assert len(results) == 5
        for r in results:
            assert r["persona"] == self.PERSONA
            assert isinstance(r["response"], str) and len(r["response"]) > 5

    def test_intelligence_extraction(self):
        results = _run_conversation(self.MESSAGES, self.PERSONA)
        bank_accounts = _collect_intel(results, "bank_accounts")
        assert len(bank_accounts) >= 1, "Should extract bank account number"

    def test_keyword_extraction(self):
        keywords = _collect_keywords(_run_conversation(self.MESSAGES, self.PERSONA))
        expected = {"bank", "account", "blocked", "kyc"}
        assert expected.issubset(keywords), f"Missing keywords: {expected - keywords}"


# ---------------------------------------------------------------------------
# 2. Busy Professional — UPI Fraud
# ---------------------------------------------------------------------------

class TestBusyProfessionalUpiFraud:
    """Simulates a UPI fraud scam against the busy_professional persona."""

    PERSONA = "busy_professional"
    SCAM_TYPE = "upi_fraud"
    MESSAGES = [
        "Your UPI payment of Rs 15000 failed. Verify by sending Rs 1 to verify@paytm.",
        "This is from your bank. Confirm your UPI account by sharing the OTP immediately.",
        "Urgent: Your UPI ID has been compromised. Send OTP to secure your UPI account now.",
        "Pay Rs 99 processing fee to refund your failed UPI payment. UPI ID: scammer@ybl",
    ]

    def test_scam_type_detected(self):
        assert quick_scam_type(self.MESSAGES[0]) == self.SCAM_TYPE

    def test_persona_mapping(self):
        assert self.PERSONA in PERSONA_MAPPING[self.SCAM_TYPE]

    def test_first_message_detected_as_scam(self):
        result = _fallback_response(self.MESSAGES[0], self.PERSONA, msg_count=1)
        assert result["is_scam"] is True
        assert result["scam_type"] == self.SCAM_TYPE

    def test_multi_turn_responses_generated(self):
        results = _run_conversation(self.MESSAGES, self.PERSONA)
        assert len(results) == 4
        for r in results:
            assert r["persona"] == self.PERSONA
            assert isinstance(r["response"], str) and len(r["response"]) > 5

    def test_intelligence_extraction(self):
        upi_ids = _collect_intel(
            _run_conversation(self.MESSAGES, self.PERSONA), "upi_ids"
        )
        assert len(upi_ids) >= 1, "Should extract at least one UPI ID"

    def test_keyword_extraction(self):
        keywords = _collect_keywords(_run_conversation(self.MESSAGES, self.PERSONA))
        assert "upi" in keywords
        assert "payment" in keywords


# ---------------------------------------------------------------------------
# 3. Curious Student — Phishing
# ---------------------------------------------------------------------------

class TestCuriousStudentPhishing:
    """Simulates a phishing scam against the curious_student persona."""

    PERSONA = "curious_student"
    SCAM_TYPE = "phishing"
    MESSAGES = [
        "Congratulations! Click this link to claim your prize: http://prize-scam.xyz/claim",
        "Verify your identity at http://fake-bank-login.com/verify to receive your cashback.",
        "Your account will be suspended. Click http://urgent-fix.net/secure immediately.",
        "Download this security update: http://malware-site.org/update to protect your device.",
        "Last chance! Click http://final-offer.biz/claim or lose your prize forever.",
    ]

    def test_scam_type_detected(self):
        assert quick_scam_type(self.MESSAGES[0]) == self.SCAM_TYPE

    def test_persona_mapping(self):
        assert self.PERSONA in PERSONA_MAPPING[self.SCAM_TYPE]

    def test_first_message_detected_as_scam(self):
        result = _fallback_response(self.MESSAGES[0], self.PERSONA, msg_count=1)
        assert result["is_scam"] is True
        assert result["scam_type"] == self.SCAM_TYPE

    def test_multi_turn_responses_generated(self):
        results = _run_conversation(self.MESSAGES, self.PERSONA)
        assert len(results) == 5
        for r in results:
            assert r["persona"] == self.PERSONA
            assert isinstance(r["response"], str) and len(r["response"]) > 5

    def test_intelligence_extraction(self):
        links = _collect_intel(
            _run_conversation(self.MESSAGES, self.PERSONA), "phishing_links"
        )
        assert len(links) >= 3, f"Should extract phishing links, got {len(links)}"

    def test_keyword_extraction(self):
        keywords = _collect_keywords(_run_conversation(self.MESSAGES, self.PERSONA))
        assert "http" in keywords or "link" in keywords or "click" in keywords


# ---------------------------------------------------------------------------
# 4. Tech-Naive Parent — Tech Support Scam
# ---------------------------------------------------------------------------

class TestTechNaiveParentTechSupport:
    """Simulates a tech-support scam against the tech_naive_parent persona."""

    PERSONA = "tech_naive_parent"
    SCAM_TYPE = "tech_support"
    MESSAGES = [
        "Alert! Your computer has been hacked by a virus. Call Microsoft support immediately at 9876543210.",
        "We detected a virus on your device. Download our Microsoft security tool to fix it now.",
        "Your Microsoft account has been compromised. Verify your identity by sharing your password.",
        "Pay Rs 2000 fee for virus removal. Send UPI payment to fix@paytm.",
    ]

    def test_scam_type_detected(self):
        assert quick_scam_type(self.MESSAGES[0]) == self.SCAM_TYPE

    def test_persona_mapping(self):
        assert self.PERSONA in PERSONA_MAPPING[self.SCAM_TYPE]

    def test_first_message_detected_as_scam(self):
        result = _fallback_response(self.MESSAGES[0], self.PERSONA, msg_count=1)
        assert result["is_scam"] is True
        assert result["scam_type"] == self.SCAM_TYPE

    def test_multi_turn_responses_generated(self):
        results = _run_conversation(self.MESSAGES, self.PERSONA)
        assert len(results) == 4
        for r in results:
            assert r["persona"] == self.PERSONA
            assert isinstance(r["response"], str) and len(r["response"]) > 5

    def test_phone_extraction(self):
        phones = _collect_intel(
            _run_conversation(self.MESSAGES, self.PERSONA), "phone_numbers"
        )
        assert len(phones) >= 1, "Should extract phone number from scammer message"

    def test_upi_extraction(self):
        upi_ids = _collect_intel(
            _run_conversation(self.MESSAGES, self.PERSONA), "upi_ids"
        )
        assert len(upi_ids) >= 1, "Should extract UPI ID from payment request"


# ---------------------------------------------------------------------------
# 5. Desperate Job Seeker — Job Scam
# ---------------------------------------------------------------------------

class TestDesperateJobSeekerJobScam:
    """Simulates a job scam against the desperate_job_seeker persona."""

    PERSONA = "desperate_job_seeker"
    SCAM_TYPE = "job_scam"
    MESSAGES = [
        "Congratulations! You've been selected for a work from home job with a salary of Rs 50000/month.",
        "To confirm your job selection, pay a registration fee of Rs 5000 via UPI to hr@axisbank.",
        "Your job training starts tomorrow. Pay Rs 3000 training fee. This is urgent.",
        "Send your bank account details for salary deposit. Account number and IFSC required.",
        "Final step: Share OTP sent to your phone 8765432109 to complete the hiring process.",
    ]

    def test_scam_type_detected(self):
        assert quick_scam_type(self.MESSAGES[0]) == self.SCAM_TYPE

    def test_persona_mapping(self):
        assert self.PERSONA in PERSONA_MAPPING[self.SCAM_TYPE]

    def test_first_message_detected_as_scam(self):
        result = _fallback_response(self.MESSAGES[0], self.PERSONA, msg_count=1)
        assert result["is_scam"] is True
        assert result["scam_type"] == self.SCAM_TYPE

    def test_multi_turn_responses_generated(self):
        results = _run_conversation(self.MESSAGES, self.PERSONA)
        assert len(results) == 5
        for r in results:
            assert r["persona"] == self.PERSONA
            assert isinstance(r["response"], str) and len(r["response"]) > 5

    def test_intelligence_extraction(self):
        results = _run_conversation(self.MESSAGES, self.PERSONA)
        upi_ids = _collect_intel(results, "upi_ids")
        phones = _collect_intel(results, "phone_numbers")
        assert len(upi_ids) >= 1, "Should extract UPI ID from registration fee message"
        assert len(phones) >= 1, "Should extract phone number from hiring message"

    def test_keyword_extraction(self):
        keywords = _collect_keywords(_run_conversation(self.MESSAGES, self.PERSONA))
        expected = {"job", "selected", "salary", "fee"}
        assert expected.issubset(keywords), f"Missing keywords: {expected - keywords}"

    def test_stage_progression(self):
        """Verify response changes as message count increases."""
        results = _run_conversation(self.MESSAGES, self.PERSONA)
        responses = [r["response"] for r in results]
        assert responses[0] != responses[2], "Responses should vary across stages"
