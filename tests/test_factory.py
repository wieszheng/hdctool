from __future__ import annotations

import pytest

import hdctool
from hdctool.factory import Hdc, create_client


def test_create_client_defaults() -> None:
    c = create_client(port=8710)
    assert c.host == "127.0.0.1"
    assert c.port == 8710
    assert c.bin == "hdc"
    assert c.connect_timeout == 30.0
    assert c.read_timeout is None
    assert c.hdc_subprocess_timeout == 120.0


def test_hdc_create_client_same_shape() -> None:
    c1 = create_client(port=9999)
    c2 = Hdc.create_client(port=9999)
    assert type(c1) is type(c2)
    assert c1.port == c2.port


def test_client_get_target_requires_key() -> None:
    c = hdctool.create_client(port=8710)
    with pytest.raises(ValueError):
        c.get_target("   ")
