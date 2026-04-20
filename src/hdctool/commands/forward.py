from __future__ import annotations

from ..command import Command
from ..types import ForwardRule
from ..util import read_ports


class ForwardPortCommand(Command[None]):
    def execute(self, local: str, remote: str) -> None:
        self.send_str(f"fport {local} {remote}")
        data = self.connection.read_value()
        result = data.decode("utf-8", errors="replace")
        if "OK" not in result:
            raise RuntimeError(result)


class ListForwardsCommand(Command[list[ForwardRule]]):
    def execute(self) -> list[dict[str, str]]:
        self.send_str("fport ls")
        data = self.connection.read_value()
        result = data.decode("utf-8", errors="replace")
        return read_ports(result, False)


class RemoveForwardPortCommand(Command[None]):
    def execute(self, local: str, remote: str) -> None:
        self.send_str(f"fport rm {local} {remote}")
        data = self.connection.read_value()
        result = data.decode("utf-8", errors="replace")
        if "success" not in result:
            raise RuntimeError(result)
