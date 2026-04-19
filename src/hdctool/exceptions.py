"""Typed errors for clearer diagnostics (connect_key / command / exit code)."""

from __future__ import annotations

from typing import Any


class HdcToolError(RuntimeError):
    """Base class for hdctool failures."""

    def __init__(self, message: str, *, context: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.context = context or {}

    def __str__(self) -> str:
        base = super().__str__()
        if not self.context:
            return base
        ctx = ", ".join(f"{k}={v!r}" for k, v in self.context.items())
        return f"{base} [{ctx}]"


class HdcTcpError(HdcToolError, ConnectionError):
    """TCP session to the local HDC server failed (also a :exc:`ConnectionError`)."""

    pass


class HdcHandshakeError(HdcToolError):
    """OHOS HDC channel handshake failed."""

    pass


class HdcSubprocessError(HdcToolError):
    """``hdc`` CLI subprocess failed or returned unexpected output."""

    def __init__(
        self,
        message: str,
        *,
        cmd: list[str] | None = None,
        returncode: int | None = None,
        stdout: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        ctx = dict(context or {})
        if cmd is not None:
            ctx["cmd"] = cmd
        if returncode is not None:
            ctx["returncode"] = returncode
        if stdout is not None:
            tail = stdout if len(stdout) < 800 else stdout[:800] + "…"
            ctx["stdout_tail"] = tail
        super().__init__(message, context=ctx)
