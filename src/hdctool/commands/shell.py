from __future__ import annotations

from ..command import Command
from ..connection import Connection


class ShellCommand(Command[Connection]):
    def execute(self, command: str) -> Connection:
        self.send_str(f"shell {command}")
        return self.connection
