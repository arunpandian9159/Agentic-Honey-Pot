"""
Monitoring and telemetry integration for AI Honeypot API.
"""

import logging
import time
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class Monitoring:
    """Simple monitoring wrapper for tracking performance."""
    
    def __init__(self):
        self.metrics = {}
    
    def track_latency(self, name: str, duration: float):
        """Track execution latency."""
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append(duration)
        logger.debug(f"Latency | {name}: {duration:.4f}s")
    
    def log_event(self, event_type: str, details: Dict[str, Any]):
        """Log a business event."""
        logger.info(f"EVENT | {event_type} | {details}")


# Singleton instance
monitor = Monitoring()
