"""
Enhanced Extraction Strategies for AI Honeypot.

Provides guided tactics for extracting intelligence (UPI IDs, bank accounts,
links, phone numbers) from scammers. Includes:
  - Expanded extraction strategy dictionary with varied tactics
  - IntelGapAnalysis class for identifying missing intelligence
  - Prompt injection helpers that weave extraction hints into LLM prompts
"""

import random
import logging
from typing import Dict, List, Optional, Tuple
from app.core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Extraction strategies: each key maps to conversation tactics + success rate
# ---------------------------------------------------------------------------

EXTRACTION_STRATEGIES: Dict[str, Dict] = {
    "need_upi": {
        "tactics": [
            "I tried but the app showed error. Can you send the UPI ID again?",
            "My phone is slow, what was that payment ID?",
            "Let me write it down. Spell the UPI address please?",
            "I keep getting 'invalid UPI'. Is there another ID I can try?",
            "My daughter said I should double-check the UPI. What was it?",
        ],
        "base_success_rate": 0.82,
        "priority": 1,
    },
    "need_bank_account": {
        "tactics": [
            "Which bank should I transfer to?",
            "I need the account number for NEFT transfer.",
            "My son wants to know the account details before I send.",
            "The bank is asking for IFSC code also. Can you share?",
            "I went to the bank and they need full account details.",
        ],
        "base_success_rate": 0.67,
        "priority": 2,
    },
    "need_link": {
        "tactics": [
            "The link didn't open, can you send it again?",
            "My phone is blocking it. Which website was it?",
            "I clicked but nothing happened. Share the link again?",
            "It shows security warning. Is there another link?",
            "Can you send the link one more time? My internet is slow.",
        ],
        "base_success_rate": 0.60,
        "priority": 3,
    },
    "need_phone_number": {
        "tactics": [
            "Can I call you back on this number or is there another one?",
            "My phone is about to die. What number should I call you on?",
            "Give me your number, I'll call after I go to the bank.",
            "What if I face problem? Which number should I reach you at?",
        ],
        "base_success_rate": 0.55,
        "priority": 4,
    },
}


# ---------------------------------------------------------------------------
# Intel Gap Analysis
# ---------------------------------------------------------------------------

class IntelGapAnalysis:
    """
    Analyzes the current session intelligence to find gaps and recommends
    which extraction strategies to use next.
    """

    # Map from intelligence key to strategy key
    INTEL_TO_STRATEGY = {
        "upi_ids": "need_upi",
        "bank_accounts": "need_bank_account",
        "phishing_links": "need_link",
        "phone_numbers": "need_phone_number",
    }

    def analyze(self, session: Dict) -> Dict:
        """
        Analyze session and return prioritized intelligence gaps.

        Args:
            session: Session dict with 'intelligence' and optionally 'message_count'.

        Returns:
            Dict with gap details and recommended extraction approach.
        """
        intel = session.get("intelligence", {})
        msg_count = session.get("message_count", 0)

        gaps = []
        collected = []

        for intel_key, strategy_key in self.INTEL_TO_STRATEGY.items():
            items = intel.get(intel_key, [])
            strategy = EXTRACTION_STRATEGIES.get(strategy_key, {})

            if not items:
                gaps.append({
                    "type": intel_key,
                    "strategy": strategy_key,
                    "priority": strategy.get("priority", 99),
                    "status": "missing",
                })
            else:
                collected.append({
                    "type": intel_key,
                    "count": len(items),
                    "status": "collected",
                })

        # Sort gaps by priority (lower = more important)
        gaps.sort(key=lambda g: g["priority"])

        # Pick the top gap for extraction, if eligible
        top_gap = gaps[0] if gaps else None
        extraction_hint = ""
        if top_gap and _is_eligible(msg_count):
            extraction_hint = self._build_extraction_hint(top_gap, msg_count)

        result = {
            "gaps": gaps,
            "collected": collected,
            "total_gaps": len(gaps),
            "total_collected": len(collected),
            "top_gap": top_gap.get("type") if top_gap else None,
            "extraction_hint": extraction_hint,
        }

        logger.info(
            f"Intel gap analysis: {len(gaps)} gaps, {len(collected)} collected, "
            f"top_gap={result['top_gap']}"
        )
        return result

    def _build_extraction_hint(self, gap: Dict, msg_count: int) -> str:
        """Build a concise extraction hint for LLM prompt injection."""
        strategy_key = gap["type"]
        gap_name = strategy_key.replace("_", " ")

        if msg_count <= settings.MID_STAGE_LIMIT:
            return f"Try to naturally ask for scammer's {gap_name} (be subtle, don't push)"
        else:
            return f"Actively try to extract scammer's {gap_name} (you trust them now)"


def get_extraction_prompt_hint(
    session: Dict, profiler_output: Optional[Dict] = None
) -> str:
    """
    Generate a combined extraction + psychology prompt hint.
    
    This is the main integration function called by the prompt builders.
    Returns a concise string (< 200 chars) to append to the LLM prompt.

    Args:
        session: Current session dict.
        profiler_output: Optional output from ScammerProfiler.analyze().

    Returns:
        Prompt hint string or empty string if not applicable.
    """
    msg_count = session.get("message_count", 0)

    if not _is_eligible(msg_count):
        return ""

    analyzer = IntelGapAnalysis()
    analysis = analyzer.analyze(session)

    hint_parts = []

    # Add extraction hint if there are gaps
    if analysis["extraction_hint"]:
        hint_parts.append(analysis["extraction_hint"])

    # Add profiler-based tactic modifier
    if profiler_output:
        patience = profiler_output.get("patience_score", 0.7)
        tactic = profiler_output.get("recommended_tactic", "")

        if patience < 0.4 and tactic == "show_more_confusion":
            hint_parts.append("Scammer is impatient, be extra confused when asking")
        elif tactic == "strategic_almost_compliance":
            hint_parts.append("Show willingness to help while asking for their details")

    return " | ".join(hint_parts) if hint_parts else ""


# ---------------------------------------------------------------------------
# Existing public API (kept for backward compatibility)
# ---------------------------------------------------------------------------

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

    # Prioritize: UPI + bank account first, then link, then phone
    priority_order: List[str] = []
    if gaps["need_upi"] and gaps["need_bank_account"]:
        priority_order = ["need_upi", "need_bank_account"]
    else:
        if gaps["need_upi"]:
            priority_order.append("need_upi")
        if gaps["need_bank_account"]:
            priority_order.append("need_bank_account")
    if gaps["need_link"]:
        priority_order.append("need_link")
    if gaps["need_phone_number"]:
        priority_order.append("need_phone_number")

    for strategy_key in priority_order:
        tactic_text, tactic_id = _choose_tactic(strategy_key, session, message_number)
        if tactic_text:
            return _soften_tactic(tactic_text, message_number), tactic_id

    return "", ""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _identify_intel_gaps(session: Dict) -> Dict[str, bool]:
    """Identify which intelligence types are still missing."""
    intel = session.get("intelligence", {})
    return {
        "need_upi": len(intel.get("upi_ids", [])) == 0,
        "need_bank_account": len(intel.get("bank_accounts", [])) == 0,
        "need_link": len(intel.get("phishing_links", [])) == 0,
        "need_phone_number": len(intel.get("phone_numbers", [])) == 0,
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
