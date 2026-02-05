from typing import Dict, Optional, Tuple
import random
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

def _intel_gaps(session: Dict) -> Dict[str, bool]:
    intel = session.get("intelligence", {})
    return {
        "need_upi": len(intel.get("upi_ids", [])) == 0,
        "need_bank_account": len(intel.get("bank_accounts", [])) == 0,
        "need_link": len(intel.get("phishing_links", [])) == 0
    }

def _eligible(message_number: int) -> bool:
    return settings.EXTRACTION_ENABLED and message_number > settings.EARLY_STAGE_LIMIT

def _cooldown_ok(session: Dict, tactic_id: str, message_number: int) -> bool:
    history = session.get("strategy_state", {}).get("tactic_history", [])
    for e in reversed(history[-10:]):
        if e.get("tactic_id") == tactic_id:
            return (message_number - int(e.get("msg", 0))) >= settings.TACTIC_COOLDOWN_MESSAGES
    return True

def _choose_tactic(strategy_key: str, session: Dict, message_number: int) -> Tuple[str, str]:
    tactics = EXTRACTION_STRATEGIES.get(strategy_key, {}).get("tactics", [])
    indices = list(range(len(tactics)))
    random.shuffle(indices)
    for idx in indices:
        tid = f"{strategy_key}:{idx}"
        if _cooldown_ok(session, tid, message_number):
            return tactics[idx], tid
    if tactics:
        return tactics[0], f"{strategy_key}:0"
    return "", ""

def _soften(text: str, message_number: int) -> str:
    if message_number <= settings.MID_STAGE_LIMIT:
        if "?" in text:
            return text
        return f"{text}?"
    return text

def get_guided_tactic(session: Dict, message_number: int, persona_name: Optional[str] = None) -> Tuple[str, str]:
    if not _eligible(message_number):
        return "", ""
    gaps = _intel_gaps(session)
    order = []
    if gaps["need_upi"] and gaps["need_bank_account"]:
        order = ["need_upi", "need_bank_account"]
    else:
        if gaps["need_upi"]:
            order.append("need_upi")
        if gaps["need_bank_account"]:
            order.append("need_bank_account")
    if gaps["need_link"]:
        order.append("need_link")
    for key in order:
        tactic_text, tactic_id = _choose_tactic(key, session, message_number)
        if tactic_text:
            return _soften(tactic_text, message_number), tactic_id
    return "", ""
