"""Subprocess-based ``hdc`` invocation (no TCP session)."""

from __future__ import annotations

import subprocess
from collections.abc import Sequence

from .exceptions import HdcSubprocessError
from .log import get_logger

_log = get_logger("hdc_cli")


def run_hdc(
    bin: str,
    connect_key: str | None,
    args: Sequence[str],
    *,
    timeout: float | None,
) -> subprocess.CompletedProcess[bytes]:
    cmd: list[str] = [bin]
    if connect_key:
        cmd.extend(["-t", connect_key])
    cmd.extend(args)
    _log.debug("run: %s", " ".join(cmd))
    try:
        return subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as e:
        raise HdcSubprocessError(
            f"hdc subprocess timed out after {timeout}s",
            cmd=list(cmd),
            context={"timeout": timeout},
        ) from e


def run_hdc_text(
    bin: str,
    connect_key: str | None,
    args: Sequence[str],
    *,
    timeout: float | None,
    check: bool = False,
) -> str:
    proc = run_hdc(bin, connect_key, args, timeout=timeout)
    text = proc.stdout.decode("utf-8", errors="replace") if proc.stdout else ""
    if check and proc.returncode != 0:
        raise HdcSubprocessError(
            "hdc command failed",
            cmd=[bin, *(["-t", connect_key] if connect_key else []), *args],
            returncode=proc.returncode,
            stdout=text,
        )
    return text
