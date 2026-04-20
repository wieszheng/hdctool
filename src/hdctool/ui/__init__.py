"""UI automation (Hypium / uitest RPC) built on HDC port forwarding."""

from __future__ import annotations

from .assertion import Assert
from .cv import CV, CVMatch, CVPoint
from .driver import UiDriver
from .subsystems import (
    UiAppManager,
    UiGestures,
    UiHilogBridge,
    UiScreen,
    UiStorage,
    UiSystem,
    UiUinput,
)

__all__ = [
    "Assert",
    "UiAppManager",
    "UiDriver",
    "UiGestures",
    "UiHilogBridge",
    "UiScreen",
    "UiStorage",
    "UiSystem",
    "UiUinput",
    "CV",
    "CVMatch",
    "CVPoint",
]
