"""
Global constants for AI Honeypot API.
"""

# Scam Detection Constants
DEFAULT_SCAM_CONFIDENCE_THRESHOLD = 0.65
DEFAULT_ACTION_THRESHOLD = 0.80

# Session Constants
DEFAULT_SESSION_TIMEOUT_MINUTES = 60
MAX_MESSAGES_PER_SESSION = 20
INTELLIGENCE_SCORE_THRESHOLD = 15.0

# Persona Constants
DEFAULT_PERSONA = "tech_naive_parent"

# API Constants
API_VERSION = "1.0.0"

# Scam Types
SCAM_TYPES = [
    "bank_fraud",
    "tech_support",
    "lottery",
    "investment",
    "job_fraud",
    "other"
]
