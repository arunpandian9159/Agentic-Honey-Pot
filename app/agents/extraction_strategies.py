"""
Extraction Strategies for AI Honeypot.
Provides guided tactics for extracting intelligence (UPI IDs, bank accounts, links)
from scammers based on conversation stage and intelligence gaps.
"""

import random
from typing import Dict, Optional, Tuple
from app.core.config import settings

EXTRACTION_STRATEGIES: Dict[str, Dict] = {
    "need_upi": {
        "tactics": [
            "I tried but it didn't work. Send UPI again?",
            "My app is slow. What was the ID?",
            "Let me write it down. Spell the UPI please?"
        ],
        "base_success_rate": 0.82
    },
    "need_bank_account": {
        "tactics": [
            "I need account number for my records",
            "Which bank should I transfer to?",
            "My son wants to know the account details"
        ],
        "base_success_rate": 0.67
    },
    "need_link": {
        "tactics": [
            "The link didn't open. Can you send it again?",
            "It shows error. What's the correct website?",
            "I clicked but nothing happened. Share the link again?"
        ],
        "base_success_rate": 0.6
    }
}


def get_guided_tactic(
    session: Dict,
    message_number: int,
    persona_name: Optional[str] = None
) -> Tuple[str, str]:
    """
    Get a guided extraction tactic based on intelligence gaps and conversation stage.

    Returns:
        Tuple of (tactic_text, tactic_id) or ("", "") if no tactic is appropriate.
    """
    if not _is_eligible(message_number):
        return "", ""

    gaps = _identify_intel_gaps(session)

    # Prioritize: UPI + bank account first, then link
    priority_order = []
    if gaps["need_upi"] and gaps["need_bank_account"]:
        priority_order = ["need_upi", "need_bank_account"]
    else:
        if gaps["need_upi"]:
            priority_order.append("need_upi")
        if gaps["need_bank_account"]:
            priority_order.append("need_bank_account")
    if gaps["need_link"]:
        priority_order.append("need_link")

    for strategy_key in priority_order:
        tactic_text, tactic_id = _choose_tactic(strategy_key, session, message_number)
        if tactic_text:
            return _soften_tactic(tactic_text, message_number), tactic_id

    return "", ""


def _identify_intel_gaps(session: Dict) -> Dict[str, bool]:
    """Identify which intelligence types are still missing."""
    intel = session.get("intelligence", {})
    return {
        "need_upi": len(intel.get("upi_ids", [])) == 0,
        "need_bank_account": len(intel.get("bank_accounts", [])) == 0,
        "need_link": len(intel.get("phishing_links", [])) == 0
    }


def _is_eligible(message_number: int) -> bool:
    """Check if extraction tactics are enabled and conversation is past early stage."""
    return settings.EXTRACTION_ENABLED and message_number > settings.EARLY_STAGE_LIMIT


def _is_cooldown_ok(session: Dict, tactic_id: str, message_number: int) -> bool:
    """Check if enough messages have passed since this tactic was last used."""
    history = session.get("strategy_state", {}).get("tactic_history", [])
    for entry in reversed(history[-10:]):
        if entry.get("tactic_id") == tactic_id:
            last_msg = int(entry.get("msg", 0))
            return (message_number - last_msg) >= settings.TACTIC_COOLDOWN_MESSAGES
    return True


def _choose_tactic(
    strategy_key: str, session: Dict, message_number: int
) -> Tuple[str, str]:
    """Choose a tactic that hasn't been used recently."""
    tactics = EXTRACTION_STRATEGIES.get(strategy_key, {}).get("tactics", [])
    if not tactics:
        return "", ""

    indices = list(range(len(tactics)))
    random.shuffle(indices)

    for idx in indices:
        tactic_id = f"{strategy_key}:{idx}"
        if _is_cooldown_ok(session, tactic_id, message_number):
            return tactics[idx], tactic_id

    # All on cooldown - use first one anyway
    return tactics[0], f"{strategy_key}:0"


def _soften_tactic(text: str, message_number: int) -> str:
    """Make tactic less direct in early-mid conversation stages."""
    if message_number <= settings.MID_STAGE_LIMIT:
        if "?" not in text:
            return f"{text}?"
    return text
