from __future__ import annotations

import subprocess
from abc import ABC, abstractmethod
from typing import Any

from .exceptions import HdcSubprocessError


class ExecCommand(ABC):
    def __init__(
        self,
        connect_key: str,
        bin: str = "hdc",
        *,
        subprocess_timeout: float | None = 120.0,
    ) -> None:
        self._bin = bin
        self._connect_key = connect_key
        self._subprocess_timeout = subprocess_timeout

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    def run(self, args: list[str], *, cwd: str | None = None) -> subprocess.CompletedProcess[bytes]:
        cmd = [self._bin, "-t", self._connect_key, *args]
        try:
            return subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=cwd,
                check=False,
                timeout=self._subprocess_timeout,
            )
        except subprocess.TimeoutExpired as e:
            raise HdcSubprocessError(
                "hdc 子进程执行超时",
                cmd=cmd,
                context={"timeout": self._subprocess_timeout},
            ) from e
