from typing import Dict, Optional

STAGE_GUIDANCE = {
    1: "Stage 1: Initial curiosity. Show mild concern, ask why they are contacting you.",
    2: "Stage 2: Information gathering. Ask clarifying questions about the process.",
    3: "Stage 3: Building trust. Show interest in their offer, appear helpful.",
    4: "Stage 4: Verification. Request their contact details or proof first.",
    5: "Stage 5: Hesitation. Express small doubts to keep them justifying themselves.",
    6: "Stage 6: Compliance. Slowly agree to their terms, ask for payment info.",
    7: "Stage 7: Prolonging. Raise technical issues or errors to stay engaged."
}

def get_stage_guidance(msg_count: int) -> str:
    """Get the strategic guidance based on the current message count."""
    if msg_count <= 2:
        return STAGE_GUIDANCE[1]
    elif msg_count <= 4:
        return STAGE_GUIDANCE[2]
    elif msg_count <= 6:
        return STAGE_GUIDANCE[3]
    elif msg_count <= 8:
        return STAGE_GUIDANCE[4]
    elif msg_count <= 10:
        return STAGE_GUIDANCE[5]
    elif msg_count <= 13:
        return STAGE_GUIDANCE[6]
    else:
        return STAGE_GUIDANCE[7]


class NaturalConversationFlow:
    """Manages the natural progression of a honeypot conversation."""
    def __init__(self):
        pass
        
    def get_guidance(self, session: Dict) -> str:
        """Calculate and return guidance for the next message."""
        count = session.get("message_count", 0)
        return get_stage_guidance(count)

__all__ = ["NaturalConversationFlow", "get_stage_guidance"]
