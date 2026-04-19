from __future__ import annotations

import re
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any

from .events import EventEmitter

if TYPE_CHECKING:
    from .command import Command

_REG_ENTRY_START = re.compile(r"\d{10}\.\d{3}\s+\d+\s+\d+")
_REG_ENTRY = re.compile(
    r"^(\d{10}\.\d{3})\s+(\d+)\s+(\d+)\s+([DIWEF])\s+([AICKP])(.{5})/([^:]*):(.*)"
)

_LEVEL_INDEX = ["?", "?", "V", "D", "I", "W", "E", "F"]
_TYPE_INDEX = ["A", "I", "C", "K", "P"]


def _to_level(letter: str) -> int:
    try:
        return _LEVEL_INDEX.index(letter)
    except ValueError:
        return -1


def _to_type(type_prefix: str) -> int:
    try:
        return _TYPE_INDEX.index(type_prefix)
    except ValueError:
        return -1


@dataclass
class HilogEntry:
    date: datetime | None = None
    pid: int = -1
    tid: int = -1
    level: int = -1
    type: int = -1
    domain: str = ""
    tag: str = ""
    message: str = ""


class Hilog(EventEmitter):
    def __init__(self, command: Command[Any]) -> None:
        super().__init__()
        self._command = command
        self._ended = False
        self._data = ""
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._read_loop, name="hdctool-hilog", daemon=True)
        self._thread.start()

    def end(self) -> None:
        self._ended = True
        self._stop.set()
        self._command.connection.end()
        self._thread.join(timeout=10.0)

    def _read_loop(self) -> None:
        try:
            while not self._stop.is_set():
                buf = self._command.connection.read_value()
                self._parse(buf)
        except Exception:
            if not self._ended:
                raise

    def _parse(self, buf: bytes) -> None:
        self._data += buf.decode("utf-8", errors="replace")
        data = self._data
        matches = list(_REG_ENTRY_START.finditer(data))
        raw_entries: list[str] = []
        for i in range(len(matches) - 1):
            s = matches[i].start()
            e = matches[i + 1].start()
            raw_entries.append(data[s:e])

        for raw_entry in raw_entries:
            entry = self._parse_entry(raw_entry)
            if entry:
                self.emit("entry", entry)

        if matches:
            self._data = data[matches[-1].start() :]
        else:
            self._data = ""

    def _parse_entry(self, raw_entry: str) -> HilogEntry | None:
        m = _REG_ENTRY.match(raw_entry)
        if not m:
            return None
        ts = float(m.group(1))
        entry = HilogEntry(
            date=datetime.fromtimestamp(ts),
            pid=int(m.group(2)),
            tid=int(m.group(3)),
            level=_to_level(m.group(4)),
            type=_to_type(m.group(5)),
            domain=m.group(6),
            tag=m.group(7),
            message=m.group(8).strip(),
        )
        return entry
