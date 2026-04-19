from __future__ import annotations

import pathlib

from ..exceptions import HdcSubprocessError
from ..exec_command import ExecCommand


class InstallCommand(ExecCommand):
    def execute(self, hap: str) -> None:
        proc = self.run(["install", str(pathlib.Path(hap).resolve())])
        stdout = proc.stdout.decode("utf-8", errors="replace") if proc.stdout else ""
        if proc.returncode != 0:
            raise HdcSubprocessError(
                "install 子进程失败",
                cmd=[self._bin, "-t", self._connect_key, "install", hap],
                returncode=proc.returncode,
                stdout=stdout,
            )
        if "install bundle successfully" not in stdout:
            raise HdcSubprocessError(
                "安装失败（未检测到成功标记）",
                cmd=[self._bin, "-t", self._connect_key, "install", hap],
                returncode=proc.returncode,
                stdout=stdout,
            )


class UninstallCommand(ExecCommand):
    def execute(self, bundle_name: str) -> None:
        proc = self.run(["uninstall", bundle_name])
        stdout = proc.stdout.decode("utf-8", errors="replace") if proc.stdout else ""
        if proc.returncode != 0:
            raise HdcSubprocessError(
                "uninstall 子进程失败",
                cmd=[self._bin, "-t", self._connect_key, "uninstall", bundle_name],
                returncode=proc.returncode,
                stdout=stdout,
            )
        if "uninstall bundle successfully" not in stdout:
            raise HdcSubprocessError(
                "卸载失败（未检测到成功标记）",
                cmd=[self._bin, "-t", self._connect_key, "uninstall", bundle_name],
                returncode=proc.returncode,
                stdout=stdout,
            )
