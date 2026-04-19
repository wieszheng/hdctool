from __future__ import annotations

import threading
from typing import TYPE_CHECKING

from .commands import (
    FileRecvCommand,
    FileSendCommand,
    ForwardPortCommand,
    GetParametersCommand,
    HilogCommand,
    InstallCommand,
    RemoveForwardPortCommand,
    ReversePortCommand,
    ShellCommand,
    UninstallCommand,
)
from .connection import Connection
from .hdc_cli import run_hdc_text
from .hilog import Hilog
from .types import ForwardRule, Parameters
from .util import wait_until

if TYPE_CHECKING:
    from .client import Client

_DEFAULT_SCREEN_REMOTE = "/data/local/tmp/hdctool_screen.jpeg"


class Target:
    def __init__(self, client: Client, connect_key: str) -> None:
        self.client = client
        self.connect_key = connect_key
        self._ready = False
        self._ready_lock = threading.Lock()

    def _exec_timeout(self) -> float | None:
        return self.client.hdc_subprocess_timeout

    def hdc(self, args: list[str], *, timeout: float | None = None) -> str:
        """纯 CLI：``hdc -t <connect_key> <args>``，一次性返回标准输出文本。"""
        t = self._exec_timeout() if timeout is None else timeout
        return run_hdc_text(self.client.bin, self.connect_key, args, timeout=t, check=False)

    def hdc_shell(self, command: str, *, timeout: float | None = None) -> str:
        """纯 CLI：执行 ``hdc -t … shell <command>``，适合简单命令与脚本。"""
        return self.hdc(["shell", command], timeout=timeout).strip()

    def screenshot_to_local(
        self,
        local: str,
        *,
        remote: str = _DEFAULT_SCREEN_REMOTE,
        shell_timeout: float | None = None,
        file_timeout: float | None = None,
    ) -> None:
        """设备端 ``snapshot_display`` 截图再通过 ``file recv`` 拉回本机。

        依赖设备侧 HDC 对 ``snapshot_display`` 的支持；失败时请改用 ``UiDriver`` 截屏或自行 shell。
        """
        self.hdc_shell(f"snapshot_display -f {remote}", timeout=shell_timeout)
        ft = self._exec_timeout() if file_timeout is None else file_timeout
        FileRecvCommand(
            self.connect_key,
            self.client.bin,
            subprocess_timeout=ft,
        ).execute(remote, local)

    def transport(self) -> Connection:
        with self._ready_lock:
            if not self._ready:
                wait_until(self._probe_ready, 10000, 1000)
        return self.client.connection(self.connect_key)

    def _probe_ready(self) -> bool:
        transport = self.client.connection(self.connect_key)
        try:
            transport.send(b"shell echo ready\n")
            data = transport.read_all()
            if b"E000004" not in data:
                self._ready = True
                return True
        finally:
            transport.end()
        return False

    def get_parameters(self) -> Parameters:
        transport = self.transport()
        try:
            return GetParametersCommand(transport).execute()
        finally:
            transport.end()

    def shell(self, command: str) -> Connection:
        transport = self.transport()
        return ShellCommand(transport).execute(command)

    def send_file(self, local: str, remote: str) -> None:
        FileSendCommand(
            self.connect_key,
            self.client.bin,
            subprocess_timeout=self._exec_timeout(),
        ).execute(local, remote)

    def recv_file(self, remote: str, local: str) -> None:
        FileRecvCommand(
            self.connect_key,
            self.client.bin,
            subprocess_timeout=self._exec_timeout(),
        ).execute(remote, local)

    def install(self, hap: str) -> None:
        InstallCommand(
            self.connect_key,
            self.client.bin,
            subprocess_timeout=self._exec_timeout(),
        ).execute(hap)

    def uninstall(self, bundle_name: str) -> None:
        UninstallCommand(
            self.connect_key,
            self.client.bin,
            subprocess_timeout=self._exec_timeout(),
        ).execute(bundle_name)

    def forward(self, local: str, remote: str) -> None:
        transport = self.transport()
        try:
            ForwardPortCommand(transport).execute(local, remote)
        finally:
            transport.end()

    def list_forwards(self) -> list[ForwardRule]:
        forwards = self.client.list_forwards()
        return [f for f in forwards if f["target"] == self.connect_key]

    def remove_forward(self, local: str, remote: str) -> None:
        transport = self.transport()
        try:
            RemoveForwardPortCommand(transport).execute(local, remote)
        finally:
            transport.end()

    def reverse(self, remote: str, local: str) -> None:
        transport = self.transport()
        try:
            ReversePortCommand(transport).execute(remote, local)
        finally:
            transport.end()

    def list_reverses(self) -> list[ForwardRule]:
        reverses = self.client.list_reverses()
        return [r for r in reverses if r["target"] == self.connect_key]

    def remove_reverse(self, remote: str, local: str) -> None:
        transport = self.transport()
        try:
            RemoveForwardPortCommand(transport).execute(remote, local)
        finally:
            transport.end()

    def create_ui_driver(
        self,
        sdk_path: str | None = None,
        sdk_version: str | None = None,
    ):
        from .ui.driver import UiDriver

        return UiDriver(self, sdk_path, sdk_version)

    def open_hilog(self, *, clear: bool = False) -> Hilog:
        if clear:
            conn = self.shell("hilog -r")
            conn.read_all()
            conn.end()
        transport = self.transport()
        return HilogCommand(transport).execute()
