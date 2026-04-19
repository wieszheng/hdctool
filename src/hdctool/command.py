from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from .connection import Connection

T = TypeVar("T")


class Command(ABC, Generic[T]):
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> T:
        raise NotImplementedError

    def send_str(self, command: str) -> None:
        self.connection.send(command.encode("utf-8"))
