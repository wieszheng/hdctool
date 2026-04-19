from __future__ import annotations

import os
import signal
import subprocess
import sys

from .commands import (
    ListForwardsCommand,
    ListReversesCommand,
    ListTargetsCommand,
    TrackTargetsCommand,
)
from .connection import Connection
from .hdc_cli import run_hdc_text
from .log import get_logger
from .target import Target
from .tracker import Tracker
from .types import ForwardRule
from .util import get_last_pid

_log = get_logger("client")


class Client:
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8710,
        bin: str = "hdc",
        *,
        connect_timeout: float = 30.0,
        read_timeout: float | None = None,
        hdc_subprocess_timeout: float | None = 120.0,
    ) -> None:
        self.host = host
        self.port = port
        self.bin = bin
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.hdc_subprocess_timeout = hdc_subprocess_timeout

    def connection(self, connect_key: str | None = None) -> Connection:
        conn = Connection(
            host=self.host,
            port=self.port,
            bin=self.bin,
            connect_timeout=self.connect_timeout,
            read_timeout=self.read_timeout,
        )
        return conn.connect(connect_key)

    def hdc(self, args: list[str], *, timeout: float | None = None) -> str:
        """通过本机 ``hdc`` 子进程执行命令（不带 ``-t``），例如 ``list targets``、``start``。"""
        t = self.hdc_subprocess_timeout if timeout is None else timeout
        return run_hdc_text(self.bin, None, args, timeout=t, check=False)

    def list_targets(self) -> list[str]:
        conn = self.connection()
        try:
            return ListTargetsCommand(conn).execute()
        finally:
            conn.end()

    def track_targets(self) -> Tracker:
        conn = self.connection()
        return TrackTargetsCommand(conn).execute()

    def get_target(self, connect_key: str) -> Target:
        if not (connect_key or "").strip():
            raise ValueError("connectKey is required")
        return Target(self, connect_key)

    def list_forwards(self) -> list[ForwardRule]:
        conn = self.connection()
        try:
            return ListForwardsCommand(conn).execute()
        finally:
            conn.end()

    def list_reverses(self) -> list[ForwardRule]:
        conn = self.connection()
        try:
            return ListReversesCommand(conn).execute()
        finally:
            conn.end()

    def kill(self, *, timeout: float = 30.0) -> None:
        pid = get_last_pid()
        if not pid:
            _log.debug("kill: no last hdc pid recorded")
            return
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/F", "/PID", str(pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                timeout=timeout,
            )
        else:
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError as e:
                _log.debug("kill pid %s: %s", pid, e)
