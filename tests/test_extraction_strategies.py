import pytest
from app.agents.extraction_strategies import get_guided_tactic, EXTRACTION_STRATEGIES
from app.core.config import settings

def make_session():
    return {
        "intelligence": {
            "bank_accounts": [],
            "upi_ids": [],
            "phishing_links": [],
            "phone_numbers": [],
            "suspicious_keywords": []
        },
        "strategy_state": {
            "tactic_history": [],
            "last_tactic": None
        },
        "scam_type": "upi_fraud",
        "persona": "tech_naive_parent"
    }

def test_no_guided_tactic_before_early_stage():
    session = make_session()
    text, tid = get_guided_tactic(session, settings.EARLY_STAGE_LIMIT, session.get("persona"))
    assert text == ""
    assert tid == ""

def test_need_upi_selected_when_missing():
    session = make_session()
    text, tid = get_guided_tactic(session, settings.EARLY_STAGE_LIMIT + 1, session.get("persona"))
    assert text != ""
    assert tid.startswith("need_upi") or tid.startswith("need_bank_account")

def test_cooldown_avoids_repeating_tactic():
    session = make_session()
    text1, tid1 = get_guided_tactic(session, settings.MID_STAGE_LIMIT + 1, session.get("persona"))
    session["strategy_state"]["tactic_history"].append({"tactic_id": tid1, "msg": settings.MID_STAGE_LIMIT + 1})
    text2, tid2 = get_guided_tactic(session, settings.MID_STAGE_LIMIT + 2, session.get("persona"))
    if tid1 and len(EXTRACTION_STRATEGIES.get(tid1.split(":")[0], {}).get("tactics", [])) > 1:
        assert tid2 != tid1
