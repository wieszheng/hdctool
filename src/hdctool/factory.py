"""Factory for :class:`~hdctool.client.Client` instances."""

from __future__ import annotations

import os

from .client import Client


def create_client(
    host: str = "127.0.0.1",
    port: int | None = None,
    bin: str = "hdc",
    *,
    connect_timeout: float = 30.0,
    read_timeout: float | None = None,
    hdc_subprocess_timeout: float | None = 120.0,
) -> Client:
    if port is None:
        port = int(os.environ.get("OHOS_HDC_SERVER_PORT", "8710"))
    return Client(
        host=host,
        port=port,
        bin=bin,
        connect_timeout=connect_timeout,
        read_timeout=read_timeout,
        hdc_subprocess_timeout=hdc_subprocess_timeout,
    )


class Hdc:
    """Backward-compatible entry point; prefer :func:`create_client`."""

    @staticmethod
    def create_client(
        host: str = "127.0.0.1",
        port: int | None = None,
        bin: str = "hdc",
        *,
        connect_timeout: float = 30.0,
        read_timeout: float | None = None,
        hdc_subprocess_timeout: float | None = 120.0,
    ) -> Client:
        return create_client(
            host=host,
            port=port,
            bin=bin,
            connect_timeout=connect_timeout,
            read_timeout=read_timeout,
            hdc_subprocess_timeout=hdc_subprocess_timeout,
        )
