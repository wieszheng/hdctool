from __future__ import annotations

import subprocess
from unittest.mock import patch

import pytest

from hdctool.commands.file import FileSendCommand
from hdctool.exceptions import HdcSubprocessError, HdcToolError


def test_hdctool_error_context_in_message() -> None:
    e = HdcToolError("bad", context={"k": 1})
    assert "bad" in str(e)
    assert "k=" in str(e)


def test_exec_subprocess_timeout_wraps_timeout_expired() -> None:
    def _boom(*_a: object, **_k: object) -> None:
        raise subprocess.TimeoutExpired(cmd=["hdc"], timeout=0.01)

    with patch("hdctool.exec_command.subprocess.run", _boom):
        cmd = FileSendCommand("device", subprocess_timeout=0.01)
        with pytest.raises(HdcSubprocessError, match="子进程执行超时"):
            cmd.run(["file", "send", "a", "b"])
