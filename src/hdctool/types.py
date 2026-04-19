from __future__ import annotations

from typing import TypedDict


class ForwardRule(TypedDict):
    local: str
    remote: str
    target: str


Parameters = dict[str, str]
