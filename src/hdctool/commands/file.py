from __future__ import annotations

import pathlib

from ..exceptions import HdcSubprocessError
from ..exec_command import ExecCommand


class FileRecvCommand(ExecCommand):
    def execute(self, remote: str, local: str) -> None:
        proc = self.run(["file", "recv", remote, str(pathlib.Path(local).resolve())])
        stdout = proc.stdout.decode("utf-8", errors="replace") if proc.stdout else ""
        if proc.returncode != 0:
            raise HdcSubprocessError(
                "file recv 子进程失败",
                cmd=[self._bin, "-t", self._connect_key, "file", "recv", remote, local],
                returncode=proc.returncode,
                stdout=stdout,
            )
        if "finish" not in stdout:
            raise HdcSubprocessError(
                "file recv 未成功完成（输出中无 finish）",
                cmd=[self._bin, "-t", self._connect_key, "file", "recv", remote, local],
                returncode=proc.returncode,
                stdout=stdout,
            )


class FileSendCommand(ExecCommand):
    def execute(self, local: str, remote: str) -> None:
        proc = self.run(["file", "send", str(pathlib.Path(local).resolve()), remote])
        stdout = proc.stdout.decode("utf-8", errors="replace") if proc.stdout else ""
        if proc.returncode != 0:
            raise HdcSubprocessError(
                "file send 子进程失败",
                cmd=[self._bin, "-t", self._connect_key, "file", "send", local, remote],
                returncode=proc.returncode,
                stdout=stdout,
            )
        if "finish" not in stdout:
            raise HdcSubprocessError(
                "file send 未成功完成（输出中无 finish）",
                cmd=[self._bin, "-t", self._connect_key, "file", "send", local, remote],
                returncode=proc.returncode,
                stdout=stdout,
            )
