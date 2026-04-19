from __future__ import annotations

import pathlib
import re
import tempfile
import time
from collections.abc import Callable
from typing import Any


def get_last_pid() -> int:
    p = pathlib.Path(tempfile.gettempdir()) / ".HDCServer.pid"
    if p.is_file():
        try:
            return int(p.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            return 0
    return 0


def read_targets(result: str) -> list[str]:
    if "Empty" in result:
        return []
    return [line for line in result.split("\n") if line]


def read_ports(result: str, reverse: bool = False) -> list[dict[str, Any]]:
    if "Empty" in result:
        return []
    lines = [
        line
        for line in result.split("\n")
        if line and ("Reverse" in line if reverse else "Forward" in line)
    ]
    out: list[dict[str, Any]] = []
    for line in lines:
        parts = re.split(r"\s+", line.strip())
        if len(parts) < 3:
            continue
        if reverse:
            out.append({"target": parts[0], "local": parts[2], "remote": parts[1]})
        else:
            out.append({"target": parts[0], "local": parts[1], "remote": parts[2]})
    return out


def wait_until(
    predicate: Callable[[], bool],
    timeout_ms: float = 10000,
    interval_ms: float = 1000,
) -> None:
    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(interval_ms / 1000)
    raise TimeoutError("wait_until timed out")
