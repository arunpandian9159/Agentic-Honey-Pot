"""
Extraction strategies and guided tactics for proactive intelligence gathering.
"""

from typing import Dict, List, Optional
import random

EXTRACTION_STRATEGIES = {
    "need_upi": {
        "tactics": [
            "I tried but it didn't work. Send UPI again?",
            "My app is slow. What was the ID?",
            "Let me write it down. Spell the UPI please?",
            "Can I pay via UPI? What is your ID?",
            "Is the UPI ID correct? It says invalid."
        ],
        "success_rate": 0.82
    },
    "need_bank_account": {
        "tactics": [
            "I need account number for my records",
            "Which bank should I transfer to?",
            "My son wants to know the account details",
            "Can you send the bank details clearly?",
            "I am at the bank, please send account number."
        ],
        "success_rate": 0.67
    },
    "need_link": {
        "tactics": [
            "The link you sent is not opening. Send again?",
            "Can you send the website link?",
            "I lost the link, please share it one more time.",
            "Where should I click? Send the link."
        ],
        "success_rate": 0.75
    }
}


def get_guided_tactic(strategy_type: str) -> str:
    """Get a random tactic for a specific strategy."""
    strategy = EXTRACTION_STRATEGIES.get(strategy_type)
    if not strategy:
        return "Can you explain more?"
    
    return random.choice(strategy["tactics"])


def identify_missing_intel(existing_intel: Dict) -> List[str]:
    """Identify which intelligence types are missing."""
    missing = []
    if not existing_intel.get("upi_ids"):
        missing.append("need_upi")
    if not existing_intel.get("bank_accounts"):
        missing.append("need_bank_account")
    if not existing_intel.get("phishing_links"):
        missing.append("need_link")
    return missing
