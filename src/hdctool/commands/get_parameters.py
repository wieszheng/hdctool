from __future__ import annotations

import re

from ..command import Command
from ..types import Parameters

_RE_KEYVAL = re.compile(r"^\s*(.+?) = (.+?)\r?$", re.MULTILINE)


class GetParametersCommand(Command[Parameters]):
    def execute(self) -> Parameters:
        self.send_str("shell param get")
        data = self.connection.read_all()
        text = data.decode("utf-8", errors="replace")
        params: Parameters = {}
        for m in _RE_KEYVAL.finditer(text):
            params[m.group(1)] = m.group(2)
        return params
