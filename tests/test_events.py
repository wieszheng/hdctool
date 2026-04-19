from __future__ import annotations

from hdctool.events import EventEmitter


def test_emit_calls_handlers() -> None:
    seen: list[str] = []
    e = EventEmitter()

    def h1(x: str) -> None:
        seen.append(x)

    e.on("ev", h1)
    e.emit("ev", "a")
    assert seen == ["a"]

    e.off("ev", h1)
    e.emit("ev", "b")
    assert seen == ["a"]


def test_multiple_handlers() -> None:
    acc: list[int] = []
    e = EventEmitter()

    def a() -> None:
        acc.append(1)

    def b() -> None:
        acc.append(2)

    e.on("x", a)
    e.on("x", b)
    e.emit("x")
    assert sorted(acc) == [1, 2]
