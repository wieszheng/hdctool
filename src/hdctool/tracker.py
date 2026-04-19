from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any

from .events import EventEmitter
from .util import read_targets

if TYPE_CHECKING:
    from .command import Command


class Tracker(EventEmitter):
    """Poll ``list targets`` in a background thread; emits ``add`` / ``remove`` / ``error``."""

    def __init__(self, command: Command[Any]) -> None:
        super().__init__()
        self._command = command
        self._target_list: list[str] = []
        self._ended = False
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._read_loop, name="hdctool-tracker", daemon=True)
        self._thread.start()

    def end(self) -> None:
        self._ended = True
        self._stop.set()
        self._command.connection.end()
        self._thread.join(timeout=10.0)

    def _read_loop(self) -> None:
        try:
            while not self._stop.is_set():
                self._command.send_str("list targets")
                data = self._command.connection.read_value()
                targets = read_targets(data.decode("utf-8", errors="replace"))
                self._update(targets)
                self._stop.wait(1.0)
        except Exception as e:
            if not self._ended:
                self.emit("error", e)

    def _update(self, new_list: list[str]) -> None:
        for t in new_list:
            if t not in self._target_list:
                self.emit("add", t)
        for t in self._target_list:
            if t not in new_list:
                self.emit("remove", t)
        self._target_list = list(new_list)
