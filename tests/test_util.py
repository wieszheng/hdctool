from __future__ import annotations

import pytest

from hdctool.util import read_ports, read_targets, wait_until


def test_read_targets_empty_marker() -> None:
    assert read_targets("Something Empty something") == []


def test_read_targets_lines() -> None:
    assert read_targets("a\nb\n") == ["a", "b"]


def test_read_ports_empty_marker() -> None:
    assert read_ports("Empty\n", reverse=False) == []


def test_read_ports_forward_three_columns() -> None:
    # Line must contain "Forward"; columns: target, local, remote (first three tokens used)
    text = "device1 tcp:8012 tcp:9876 Forward-extra\n"
    assert read_ports(text, reverse=False) == [
        {"target": "device1", "local": "tcp:8012", "remote": "tcp:9876"},
    ]


def test_read_ports_reverse_three_columns() -> None:
    # Line must contain "Reverse"; implementation maps local<-parts[2], remote<-parts[1]
    text = "device1 tcp:A tcp:B Reverse\n"
    assert read_ports(text, reverse=True) == [
        {"target": "device1", "local": "tcp:B", "remote": "tcp:A"},
    ]


def test_wait_until_success() -> None:
    calls = {"n": 0}

    def ok() -> bool:
        calls["n"] += 1
        return calls["n"] >= 2

    wait_until(ok, timeout_ms=5000, interval_ms=5)


def test_wait_until_timeout() -> None:
    with pytest.raises(TimeoutError):
        wait_until(lambda: False, timeout_ms=50, interval_ms=10)
