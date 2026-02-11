"""
Detection Configuration for Advanced Scam Detection System.
Contains all configurable parameters for the multi-factor detection system.
"""

# Detection thresholds
DETECTION_CONFIG = {
    # Confidence threshold for scam classification
    "confidence_threshold": 0.65,
    
    # Factor weights (must sum to 1.0)
    "factor_weights": {
        "linguistic": 0.20,
        "behavioral": 0.20,
        "technical": 0.15,
        "context": 0.10,
        "llm": 0.35
    },
    
    # False positive tolerance
    "max_false_positive_rate": 0.05,  # 5%
    
    # Minimum confidence for automatic action
    "action_threshold": 0.80,  # Only auto-engage if >80% confident
    
    # Feature flags
    "use_llm_detection": True,
    "use_linguistic_analysis": True,
    "use_behavioral_analysis": True,
    "use_technical_analysis": True,
    "use_context_analysis": True,
    
    # Performance settings
    "cache_detection_results": True,
    "detection_timeout_seconds": 5,
    
    # Score thresholds for individual factors
    "red_flag_threshold": 0.6,  # Score above this triggers red flag
    
    # LLM override settings
    "llm_high_confidence_threshold": 0.80,  # Trust LLM if this confident
}


def get_factor_weight(factor_name: str) -> float:
    """Get weight for a specific factor."""
    return DETECTION_CONFIG["factor_weights"].get(factor_name, 0.0)


def get_confidence_threshold() -> float:
    """Get the confidence threshold for scam classification."""
    return DETECTION_CONFIG["confidence_threshold"]


def is_feature_enabled(feature_name: str) -> bool:
    """Check if a feature is enabled."""
    key = f"use_{feature_name}"
    return DETECTION_CONFIG.get(key, True)
