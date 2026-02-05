from typing import Dict, List

def get_concise_context(session: Dict, msg_count: int) -> str:
    """Generate a high-level context string for LLM guidance."""
    hints = []

    if session.get("scam_detected"):
        hints.append(f"SCAM DETECTED: {session.get('scam_type', 'unknown')}")

    intel = session.get("intelligence", {})
    if intel.get("upi_ids"):
        hints.append(f"IDENTIFIED UPI: {intel['upi_ids'][0]}")
    elif intel.get("bank_accounts"):
        hints.append(f"IDENTIFIED BANK: {intel['bank_accounts'][0]}")

    return " | ".join(hints) if hints else "Analyzing scammer behavior..."


class ContextAwareManager:
    """Manages evolution of conversation based on previous context."""
    def __init__(self):
        pass
        
    def get_stage_guidance(self, message_count: int) -> str:
        """Get guidance based on conversation stage."""
        if message_count <= 2:
            return "Stage 1: Initial contact. Express mild concern and ask for clarification."
        elif message_count <= 5:
            return "Stage 2: Building trust. Ask questions about the process, appear cooperative but confused."
        elif message_count <= 10:
            return "Stage 3: Deep engagement. Ask for specific payment/verification details."
        else:
            return "Stage 4: Prolonging. Raise technical issues or small errors to keep them talking."

__all__ = ["ContextAwareManager", "get_concise_context"]
