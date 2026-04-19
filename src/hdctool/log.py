"""Optional logging via stdlib :mod:`logging`.

Set ``HDCTOOL_LOG_LEVEL`` to ``DEBUG``, ``INFO``, ``WARNING`` (default), etc.
"""

from __future__ import annotations

import logging
import os

_CONFIGURED = False
_LOGGER = logging.getLogger("hdctool")


def configure_logging() -> None:
    """Idempotent: respect ``HDCTOOL_LOG_LEVEL`` (default ``WARNING``)."""
    global _CONFIGURED
    if _CONFIGURED:
        return
    level_name = os.environ.get("HDCTOOL_LOG_LEVEL", "WARNING").upper()
    level = getattr(logging, level_name, logging.WARNING)
    if not logging.root.handlers:
        logging.basicConfig(
            level=level,
            format="%(levelname)s %(name)s: %(message)s",
        )
    else:
        _LOGGER.setLevel(level)
    _CONFIGURED = True


def get_logger(name: str | None = None) -> logging.Logger:
    configure_logging()
    if name:
        return logging.getLogger(f"hdctool.{name}")
    return _LOGGER
