"""
Logging configuration for AI Honeypot API.
Structured, color-coded, and visually scannable terminal output.
"""

import logging
import sys
from app.core.config import settings


# ── ANSI color codes for Windows terminal ────────────────────────────
class Colors:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"

    # Foreground
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    BLUE    = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN    = "\033[96m"
    WHITE   = "\033[97m"
    GRAY    = "\033[90m"

    # Background
    BG_RED  = "\033[41m"


# ── Map log levels to colored labels ─────────────────────────────────
LEVEL_STYLES = {
    "DEBUG":    f"{Colors.GRAY}DEBUG{Colors.RESET}",
    "INFO":     f"{Colors.GREEN}INFO{Colors.RESET}",
    "WARNING":  f"{Colors.YELLOW}WARN{Colors.RESET}",
    "ERROR":    f"{Colors.RED}ERROR{Colors.RESET}",
    "CRITICAL": f"{Colors.BG_RED}{Colors.WHITE}CRIT{Colors.RESET}",
}

# ── Short aliases for module names ───────────────────────────────────
MODULE_ALIASES = {
    "app.api.routes":                   "api",
    "app.core.session":                 "session",
    "app.core.llm":                     "llm",
    "app.core.rag_config":              "rag-cfg",
    "app.agents.enhanced_conversation": "conv",
    "app.agents.optimized":             "agent",
    "app.agents.scammer_profiler":      "profiler",
    "app.agents.enhanced_detector":     "detector",
    "app.agents.detector":              "detector",
    "app.agents.extractor":             "extractor",
    "app.agents.extraction_strategies": "strategy",
    "app.agents.personas":              "persona",
    "app.agents.rag_conversation_manager": "rag",
    "app.agents.conversation":          "conv",
    "app.rag.embeddings":               "embed",
    "app.rag.knowledge_store":          "store",
    "app.utils.callbacks":              "callback",
    "app.utils.rate_limiter":           "ratelim",
    "app.utils.logger":                 "logger",
    "__main__":                         "main",
    "main":                             "main",
}


class PrettyFormatter(logging.Formatter):
    """
    Structured log formatter that produces easily scannable output.

    Format:
        HH:MM:SS │ INF │ module   │ message
    """

    COL_TIME   = 8   # HH:MM:SS
    COL_LEVEL  = 3   # INF/WRN/ERR
    COL_MODULE = 10  # short alias

    def format(self, record: logging.LogRecord) -> str:
        # Time — just HH:MM:SS (date is rarely needed in dev)
        time_str = self.formatTime(record, "%H:%M:%S")

        # Level — colored 3-char label
        level = LEVEL_STYLES.get(record.levelname, record.levelname[:3])

        # Module — short alias or last segment
        module_name = record.name
        short = MODULE_ALIASES.get(module_name)
        if not short:
            short = module_name.rsplit(".", 1)[-1]
        short = short[:self.COL_MODULE].ljust(self.COL_MODULE)
        module_display = f"{Colors.CYAN}{short}{Colors.RESET}"

        # Message
        msg = record.getMessage()

        # Separator
        sep = f"{Colors.DIM}│{Colors.RESET}"

        line = f"{Colors.GRAY}{time_str}{Colors.RESET} {sep} {level} {sep} {module_display} {sep} {msg}"

        # Append exception info if present
        if record.exc_info and not record.exc_text:
            record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            line += f"\n{Colors.RED}{record.exc_text}{Colors.RESET}"

        return line


def setup_logging() -> None:
    """Configure application logging with structured, colored output."""

    # Enable ANSI colors on Windows
    _enable_windows_ansi()

    log_level = logging.DEBUG if settings.DEBUG else getattr(
        logging, settings.LOG_LEVEL.upper(), logging.INFO
    )

    # Create handler with pretty formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(PrettyFormatter())

    # Configure root logger
    root = logging.getLogger()
    root.setLevel(log_level)
    root.handlers.clear()
    root.addHandler(handler)

    # Suppress verbose third-party logs
    for noisy in ("groq", "httpx", "httpcore", "uvicorn.access",
                   "fastembed", "onnxruntime", "sentence_transformers"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info(f"Logging ready — level={settings.LOG_LEVEL}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)


def _enable_windows_ansi():
    """Enable ANSI escape sequences on Windows 10+ terminals."""
    try:
        import os
        if os.name == "nt":
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception as e:
        print(f"Failed to log message: {e}")
