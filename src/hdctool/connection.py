from __future__ import annotations

import os
import socket
import subprocess

from .channel_handshake import ChannelHandShake
from .exceptions import HdcHandshakeError, HdcTcpError
from .log import get_logger

_log = get_logger("connection")

HANDSHAKE_MESSAGE = b"OHOS HDC"


class Connection:
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8710,
        bin: str = "hdc",
        *,
        connect_timeout: float = 30.0,
        read_timeout: float | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.bin = bin
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self._sock: socket.socket | None = None
        self.ended = False
        self._tried_starting = False

    def connect(self, connect_key: str | None = None) -> Connection:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.connect_timeout)
            sock.connect((self.host, self.port))
            if self.read_timeout is not None:
                sock.settimeout(self.read_timeout)
            else:
                sock.settimeout(None)
            self._sock = sock
        except (ConnectionRefusedError, OSError, TimeoutError) as e:
            if not self._tried_starting:
                self._tried_starting = True
                self._start_server()
                return self.connect(connect_key)
            self.end()
            raise HdcTcpError(
                f"无法连接 HDC 服务 {self.host}:{self.port}",
                context={"host": self.host, "port": self.port, "connect_key": connect_key},
            ) from e
        try:
            self._handshake(connect_key)
        except Exception:
            self.end()
            raise
        _log.debug("connected handshake ok connect_key=%r", connect_key)
        return self

    def end(self) -> None:
        self.ended = True
        if self._sock is not None:
            try:
                self._sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None

    def write(self, data: bytes) -> None:
        if self._sock is None:
            raise ConnectionError("not connected")
        self._sock.sendall(data)

    def send(self, data: bytes) -> None:
        length = len(data).to_bytes(4, "big")
        self.write(length + data)

    def read_bytes(self, how_many: int) -> bytes:
        if self._sock is None:
            raise ConnectionError("not connected")
        if how_many == 0:
            return b""
        buf = b""
        while len(buf) < how_many:
            try:
                chunk = self._sock.recv(how_many - len(buf))
            except TimeoutError as e:
                raise HdcTcpError(
                    "套接字读取超时",
                    context={"expected_bytes": how_many, "received": len(buf)},
                ) from e
            if not chunk:
                self.ended = True
                raise HdcTcpError(
                    "连接已关闭（对端结束）",
                    context={"expected_bytes": how_many, "received": len(buf)},
                )
            buf += chunk
        return buf

    def read_value(self) -> bytes:
        head = self.read_bytes(4)
        length = int.from_bytes(head, "big")
        return self.read_bytes(length)

    def read_all(self) -> bytes:
        chunks: list[bytes] = []
        while True:
            try:
                chunk = self.read_value()
                chunks.append(chunk)
            except ConnectionError:
                if self.ended:
                    return b"".join(chunks)
                raise

    def _handshake(self, connect_key: str | None) -> None:
        data = self.read_value()
        hs = ChannelHandShake()
        hs.deserialize(data)
        if not hs.banner.startswith(HANDSHAKE_MESSAGE):
            raise HdcHandshakeError(
                "Channel Hello 失败：banner 不符合预期",
                context={"connect_key": connect_key, "banner_prefix": hs.banner[:24]},
            )
        if connect_key is not None:
            hs.connect_key = connect_key
        self.send(hs.serialize())

    def _start_server(self) -> None:
        env = {**os.environ, "OHOS_HDC_SERVER_PORT": str(self.port)}
        try:
            subprocess.run(
                [self.bin, "start"],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                timeout=60.0,
            )
        except subprocess.TimeoutExpired:
            _log.warning("hdc start timed out (60s)")
