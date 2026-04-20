"""
hdctool — synchronous Python client for OpenHarmony **HDC** (device connector).

Public API is re-exported from this package; implementation lives under
``hdctool.commands``, ``hdctool.ui``, etc.
"""

from __future__ import annotations

from .client import Client
from .exceptions import HdcHandshakeError, HdcSubprocessError, HdcTcpError, HdcToolError
from .factory import Hdc, create_client
from .hilog import Hilog, HilogEntry
from .log import configure_logging, get_logger
from .ui import CV, Assert, CVMatch, CVPoint, UiDriver
from .version import __version__

__all__ = [
    "Assert",
    "Client",
    "Hdc",
    "HdcHandshakeError",
    "HdcSubprocessError",
    "HdcTcpError",
    "HdcToolError",
    "Hilog",
    "HilogEntry",
    "UiDriver",
    "CV",
    "CVMatch",
    "CVPoint",
    "__version__",
    "configure_logging",
    "create_client",
    "get_logger",
]
