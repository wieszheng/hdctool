from __future__ import annotations

import hdctool


def test_version() -> None:
    assert isinstance(hdctool.__version__, str)
    parts = hdctool.__version__.split(".")
    assert len(parts) >= 2


def test_create_client() -> None:
    c = hdctool.create_client(port=65533)
    assert c.port == 65533


def test_public_exports() -> None:
    names = {
        "Client",
        "Hdc",
        "HdcHandshakeError",
        "HdcSubprocessError",
        "HdcTcpError",
        "HdcToolError",
        "Hilog",
        "HilogEntry",
        "UiDriver",
        "configure_logging",
        "create_client",
        "get_logger",
        "__version__",
    }
    assert names <= set(dir(hdctool))
