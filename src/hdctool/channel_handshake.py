from __future__ import annotations

MAX_CONNECTKEY_SIZE = 32


class ChannelHandShake:
    def __init__(self) -> None:
        self.banner: bytes = b""
        self.channel_id: int = 0
        self.connect_key: str = ""

    def deserialize(self, buf: bytes) -> None:
        self.banner = buf[0:12]
        self.channel_id = int.from_bytes(buf[12:16], "big")

    def serialize(self) -> bytes:
        key = self.connect_key.encode("utf-8")[:MAX_CONNECTKEY_SIZE]
        connect_key = key.ljust(MAX_CONNECTKEY_SIZE, b"\x00")
        return self.banner + connect_key
