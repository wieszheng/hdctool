from __future__ import annotations

from ..command import Command
from ..hilog import Hilog


class HilogCommand(Command[Hilog]):
    def execute(self) -> Hilog:
        self.send_str("shell hilog -v wrap -v epoch")
        return Hilog(self)
