"""
Structured logging setup.
Call `setup_logging()` once at application startup.
"""
 
from __future__ import annotations
 
import logging
import sys
from typing import Any
 
from app.core.config import settings
 
 
class _JsonFormatter(logging.Formatter):
    """Minimal JSON formatter (no external deps required)."""
 
    def format(self, record: logging.LogRecord) -> str:
        import json
        import traceback
 
        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "time": self.formatTime(record, self.datefmt),
        }
        if record.exc_info:
            payload["exc_info"] = traceback.format_exception(*record.exc_info)
        if hasattr(record, "extra"):
            payload.update(record.extra)  # type: ignore[arg-type]
        return json.dumps(payload, ensure_ascii=False)
 
 
def setup_logging() -> None:
    """Configure root logger; call once from main.py lifespan."""
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
 
    handler = logging.StreamHandler(sys.stdout)
    if settings.log_json:
        handler.setFormatter(_JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S",
            )
        )
 
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
 
    # Silence noisy third-party loggers
    for noisy in ("PIL", "urllib3", "httpx", "mediapipe"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
 
 
def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)