from __future__ import annotations

from ..command import Command
from ..types import ForwardRule
from ..util import read_ports


class ReversePortCommand(Command[None]):
    def execute(self, remote: str, local: str) -> None:
        self.send_str(f"rport {remote} {local}")
        data = self.connection.read_value()
        result = data.decode("utf-8", errors="replace")
        if "OK" not in result:
            raise RuntimeError(result)


class ListReversesCommand(Command[list[ForwardRule]]):
    def execute(self) -> list[ForwardRule]:
        self.send_str("fport ls")
        data = self.connection.read_value()
        result = data.decode("utf-8", errors="replace")
        return read_ports(result, True)
