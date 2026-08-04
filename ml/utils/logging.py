"""Logging helpers for the ML platform.

Provides a consistent logger factory and a one-time ``configure_logging``
that can be called from the CLI or pipeline entry points. Logs are
structured-friendly (extra fields) and can be switched to JSON.
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any, Dict, Optional


class JsonFormatter(logging.Formatter):
    """A minimal JSON log formatter for pipeline runs."""

    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key.startswith("_") or key in (
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "taskName",
                "message",
                "asctime",
            ):
                continue
            try:
                json.dumps(value)  # ensure serialisable
            except (TypeError, ValueError):
                value = str(value)
            payload[key] = value
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload)


_configured = False


def configure_logging(level: int = logging.INFO, json_logs: bool = False) -> None:
    """Configure the root logger once (idempotent)."""
    global _configured
    if _configured:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter() if json_logs else logging.Formatter(
        "%(asctime)s %(levelname)-7s %(name)s: %(message)s"
    ))
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers = [handler]
    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a logger for the given module name."""
    return logging.getLogger(name)
