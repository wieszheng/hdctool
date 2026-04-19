"""Minimal publish–subscribe helper for device events (logs, target list, UI stream)."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from typing import Any


class EventEmitter:
    def __init__(self) -> None:
        self._handlers: defaultdict[str, list[Callable[..., Any]]] = defaultdict(list)

    def on(self, event: str, fn: Callable[..., Any]) -> None:
        self._handlers[event].append(fn)

    def off(self, event: str, fn: Callable[..., Any]) -> None:
        if event in self._handlers and fn in self._handlers[event]:
            self._handlers[event].remove(fn)

    def emit(self, event: str, *args: Any) -> None:
        for fn in list(self._handlers.get(event, [])):
            fn(*args)
