from __future__ import annotations

from ..command import Command
from ..tracker import Tracker
from ..util import read_targets


class ListTargetsCommand(Command[list[str]]):
    def execute(self) -> list[str]:
        self.send_str("list targets")
        data = self.connection.read_value()
        return read_targets(data.decode("utf-8", errors="replace"))


class TrackTargetsCommand(Command[Tracker]):
    def execute(self) -> Tracker:
        self.send_str("alive")
        return Tracker(self)
