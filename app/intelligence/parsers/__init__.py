"""
Scam intelligence parsers package.
"""

from app.intelligence.parsers.bank_parser import BankAccountParser
from app.intelligence.parsers.upi_parser import UPIParser
from app.intelligence.parsers.phone_parser import PhoneParser
from app.intelligence.parsers.url_parser import URLParser
from app.intelligence.parsers.llm_parser import LLMParser
from app.intelligence.parsers.extraction_strategies import EXTRACTION_STRATEGIES

__all__ = [
    "BankAccountParser",
    "UPIParser",
    "PhoneParser",
    "URLParser",
    "LLMParser",
    "EXTRACTION_STRATEGIES"
]
