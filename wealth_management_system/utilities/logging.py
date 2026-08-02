"""Logging configuration helpers.

All engines log through :func:`get_logger` so that:

* every module gets a properly-namespaced logger,
* logs carry a consistent format including level and timestamp,
* the whole application can be configured from one place via
  :func:`setup_logging`.

There are no global mutable singletons — configuration is stored on the
root logger only, which is the Python logging idiom.
"""

from __future__ import annotations

import logging
import sys

_DEFAULT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_configured = False


def setup_logging(
    level: int = logging.INFO,
    *,
    format_string: str = _DEFAULT_FORMAT,
    date_format: str = _DEFAULT_DATE_FORMAT,
) -> None:
    """Configure the root logger for the application.

    Idempotent — repeated calls reconfigure the handlers in place rather
    than stacking duplicates.

    Parameters
    ----------
    level:
        Root logging level (e.g. ``logging.INFO``).
    format_string:
        Log line format.
    date_format:
        Timestamp format used inside ``format_string``.
    """
    global _configured

    root = logging.getLogger()
    root.setLevel(level)

    # replace existing handlers to avoid duplicates on reconfiguration
    for handler in list(root.handlers):
        root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(format_string, date_format))
    root.addHandler(handler)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced logger for a module.

    Parameters
    ----------
    name:
        Usually ``__name__`` of the calling module.

    Returns
    -------
    logging.Logger
        A logger whose handlers are controlled by the root logger. If
        :func:`setup_logging` has never been called, a basic config is
        applied once so log lines still appear.
    """
    global _configured
    if not _configured:
        setup_logging()
    return logging.getLogger(name)
