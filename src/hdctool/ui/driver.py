from __future__ import annotations

import concurrent.futures
import inspect
import json
import pathlib
import socket
import threading
import time
import zlib
from collections.abc import Callable
from functools import cached_property
from typing import Any

from ..events import EventEmitter
from ..target import Target
from .subsystems import (
    UiAppManager,
    UiGestures,
    UiHilogBridge,
    UiScreen,
    UiStorage,
    UiSystem,
    UiUinput,
)

# Package root (…/hdctool/), sibling to ``uitestkit_sdk/``
_PKG_ROOT = pathlib.Path(__file__).resolve().parent.parent
SDK_PATH_DEFAULT = _PKG_ROOT / "uitestkit_sdk" / "uitest_agent_v1.1.0.so"
SDK_VERSION_DEFAULT = "1.1.0"
AGENT_PATH = "/data/local/tmp/agent.so"

HEADER_BYTES = b"_uitestkit_rpc_message_head_"
TAILER_BYTES = b"_uitestkit_rpc_message_tail_"


def _cmp_version(a: str, b: str) -> int:
    def parts(s: str) -> list[int]:
        out: list[int] = []
        for x in s.split("."):
            try:
                out.append(int(x))
            except ValueError:
                out.append(0)
        return out

    from itertools import zip_longest

    for x, y in zip_longest(parts(a), parts(b), fillvalue=0):
        if x != y:
            return -1 if x < y else 1
    return 0


def _session_id(payload: str) -> int:
    return zlib.crc32(f"{time.time()}{payload}".encode()) & 0xFFFFFFFF


def _sync_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


class _RpcConnection:
    def __init__(self) -> None:
        self._sock: socket.socket | None = None
        self._ended = False
        self._buffer = bytearray()
        self._on_message: Callable[[int, bytes], None] | None = None
        self._pending: dict[int, concurrent.futures.Future] = {}
        self._pending_lock = threading.Lock()

    def connect(self, port: int) -> None:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("127.0.0.1", port))
        self._sock = s

    def set_on_message(self, fn: Callable[[int, bytes], None]) -> None:
        self._on_message = fn

    def pump(self) -> None:
        assert self._sock is not None
        while not self._ended:
            try:
                chunk = self._sock.recv(65536)
                if not chunk:
                    self._ended = True
                    break
                self._on_data(chunk)
            except OSError:
                break

    def end(self) -> None:
        self._ended = True
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

    def send_raw_message(self, session_id_buf: bytes, message: bytes) -> None:
        if self._ended or self._sock is None:
            raise ConnectionError("ended")
        out = (
            HEADER_BYTES + session_id_buf + len(message).to_bytes(4, "big") + message + TAILER_BYTES
        )
        self._sock.sendall(out)

    def send_message(self, message: dict[str, Any], timeout: float = 0) -> dict[str, Any]:
        raw = json.dumps(message, separators=(",", ":"))
        sid = _session_id(raw)
        sid_buf = sid.to_bytes(4, "big")
        fut: concurrent.futures.Future = concurrent.futures.Future()
        with self._pending_lock:
            self._pending[sid] = fut
        self.send_raw_message(sid_buf, raw.encode("utf-8"))
        try:
            if timeout and timeout > 0:
                return fut.result(timeout=timeout)
            return fut.result()
        except concurrent.futures.TimeoutError:
            with self._pending_lock:
                self._pending.pop(sid, None)
            raise TimeoutError from None
        except BaseException:
            with self._pending_lock:
                self._pending.pop(sid, None)
            raise

    def _on_data(self, data: bytes) -> None:
        buf = self._buffer
        buf.extend(data)

        while len(buf) >= len(HEADER_BYTES) + 8:
            if bytes(buf[0 : len(HEADER_BYTES)]) != HEADER_BYTES:
                buf.clear()
                break

            if len(buf) < len(HEADER_BYTES) + 8:
                break

            session_id = int.from_bytes(buf[len(HEADER_BYTES) : len(HEADER_BYTES) + 4], "big")
            ln = int.from_bytes(buf[len(HEADER_BYTES) + 4 : len(HEADER_BYTES) + 8], "big")
            total = len(HEADER_BYTES) + 8 + ln + len(TAILER_BYTES)

            if len(buf) < total:
                break

            start = len(HEADER_BYTES) + 8
            end = start + ln
            message = bytes(buf[start:end])
            tail = bytes(buf[end : end + len(TAILER_BYTES)])
            if tail != TAILER_BYTES:
                buf.clear()
                break

            with self._pending_lock:
                fut = self._pending.pop(session_id, None)
            if fut is not None and not fut.done():
                try:
                    result = json.loads(message.decode("utf-8"))
                    if isinstance(result, dict) and result.get("exception"):
                        exc = result["exception"]
                        if isinstance(exc, dict) and "message" in exc:
                            fut.set_exception(RuntimeError(str(exc["message"])))
                        else:
                            fut.set_exception(RuntimeError(str(result)))
                    elif isinstance(result, dict):
                        fut.set_result({"sessionId": session_id, "result": result.get("result")})
                    else:
                        fut.set_result({"sessionId": session_id, "result": message})
                except json.JSONDecodeError:
                    fut.set_result({"sessionId": session_id, "result": message})
            elif self._on_message:
                self._on_message(session_id, message)

            del buf[:total]

        self._buffer = buf


class UiDriver(EventEmitter):
    def __init__(
        self,
        target: Target,
        sdk_path: str | pathlib.Path | None = None,
        sdk_version: str | None = None,
    ) -> None:
        super().__init__()
        self._target = target
        self._connection: _RpcConnection | None = None
        self._driver_name = ""
        self._port = 0
        self._sdk_version = sdk_version or SDK_VERSION_DEFAULT
        self._sdk_path = pathlib.Path(sdk_path) if sdk_path else SDK_PATH_DEFAULT
        self._tried_starting = False
        self._capture_cb: Callable[[int, bytes], None] | None = None
        self._conn_lock = threading.Lock()
        self._pump_thread: threading.Thread | None = None

    @property
    def target(self) -> Target:
        """当前 :class:`~hdctool.target.Target`（供子系统与外部直接调用 HDC 能力）。"""
        return self._target

    @cached_property
    def gestures(self) -> UiGestures:
        """手势与键鼠、表冠等。"""
        return UiGestures(self)

    @cached_property
    def app_manager(self) -> UiAppManager:
        """应用安装、进程/包信息、清数据等。"""
        return UiAppManager(self)

    @cached_property
    def screen(self) -> UiScreen:
        """亮灭屏、方向、休眠时间、截屏/录屏流等。"""
        return UiScreen(self)

    @cached_property
    def storage(self) -> UiStorage:
        """设备文件 push/pull/has/rm。"""
        return UiStorage(self)

    @cached_property
    def system(self) -> UiSystem:
        """系统参数与 shell 级能力。"""
        return UiSystem(self)

    @cached_property
    def hilog(self) -> UiHilogBridge:
        """hilog 流与 listener。"""
        return UiHilogBridge(self)

    @cached_property
    def uinput(self) -> UiUinput:
        """键值注入等。"""
        return UiUinput(self)

    def call_driver(self, api: str, args: Any | None = None) -> Any:
        """调用 ``Driver.<api>``，返回 RPC 的 ``result`` 字段（无则为 ``None``）。"""
        if args is None:
            args = []
        r = self._send("callHypiumApi", api, args)
        return r.get("result")

    def call_rpc(self, method: str, api: str, args: Any | None = None) -> Any:
        """调用 uitest RPC（``method`` 如 ``Gestures`` / ``Captures``，``api`` 为方法名）。"""
        if args is None:
            args = {}
        r = self._send(method, api, args)
        return r.get("result")

    def start(self) -> None:
        ui_pid = self._shell("pidof uitest").strip()
        should_update = self._should_update_sdk()
        if not ui_pid or should_update:
            self._shell("param set persist.ace.testmode.enabled 1")
            if should_update:
                if ui_pid:
                    self._shell(f"kill -9 {ui_pid}")
                    ui_pid = ""
                self._update_sdk()
            if not ui_pid:
                self._shell("uitest start-daemon singleness")
                time.sleep(2)
        self._port = self._forward_tcp(8012)

    def stop(self) -> None:
        if self._pump_thread is not None:
            if self._connection is not None:
                self._connection.end()
            if self._pump_thread.is_alive():
                self._pump_thread.join(timeout=10.0)
            self._pump_thread = None
        self._connection = None
        ui_pid = self._shell("pidof uitest").strip()
        if ui_pid:
            self._shell(f"kill -9 {ui_pid}")

    def start_capture_screen(
        self,
        callback: Callable[[bytes], Any],
        *,
        scale: float = 1,
    ) -> None:
        if inspect.iscoroutinefunction(callback):
            raise TypeError(
                "同步 UiDriver 不支持 async 截屏回调，请使用 def on_frame(data: bytes): ..."
            )
        opts: dict[str, Any] = {}
        if 0 < scale < 1:
            opts["scale"] = scale
        result = self._send("Captures", "startCaptureScreen", {"options": opts})
        session_id = result["sessionId"]
        if self._capture_cb:
            raise RuntimeError("Capture screen is already started")

        def _cb(sid: int, msg: bytes) -> None:
            if sid == session_id:
                callback(msg)

        self._capture_cb = _cb
        self.on("message", _cb)

    def stop_capture_screen(self) -> None:
        self._send("Captures", "stopCaptureScreen")
        if self._capture_cb:
            self.off("message", self._capture_cb)
            self._capture_cb = None

    def capture_layout(self) -> Any:
        r = self._send("Captures", "captureLayout")
        return r["result"]

    def get_display_size(self) -> Any:
        r = self._send("CtrlCmd", "getDisplaySize")
        return r["result"]

    def touch_down(self, x: float, y: float) -> None:
        self._send("Gestures", "touchDown", {"x": x, "y": y})

    def touch_move(self, x: float, y: float) -> None:
        self._send("Gestures", "touchMove", {"x": x, "y": y})

    def touch_up(self, x: float, y: float) -> None:
        self._send("Gestures", "touchUp", {"x": x, "y": y})

    def input_text(self, text: str, x: float = 0, y: float = 0) -> None:
        self._send("callHypiumApi", "inputText", [{"x": x, "y": y}, text])

    def press_back(self) -> None:
        self._send("callHypiumApi", "pressBack", [])

    def press_home(self) -> None:
        self._send("callHypiumApi", "pressHome", [])

    def click(self, x: float, y: float) -> None:
        self._send("callHypiumApi", "click", [{"x": x, "y": y}])

    def double_click(self, x: float, y: float) -> None:
        self._send("callHypiumApi", "doubleClick", [{"x": x, "y": y}])

    def long_click(self, x: float, y: float, duration_ms: int = 1500) -> None:
        self._send("callHypiumApi", "longClick", [{"x": x, "y": y}, duration_ms])

    def start_app(self, bundle_name: str) -> None:
        self._send("callHypiumApi", "startApp", [bundle_name])

    def stop_app(self, bundle_name: str) -> None:
        self._send("callHypiumApi", "stopApp", [bundle_name])

    def swipe(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        duration_ms: int = 300,
    ) -> None:
        self._send(
            "callHypiumApi",
            "swipe",
            [{"x": x1, "y": y1}, {"x": x2, "y": y2}, duration_ms],
        )

    def _send(self, method: str, api: str, args: Any = None) -> dict[str, Any]:
        if args is None:
            args = {}
        module = "com.ohos.devicetest.hypiumApiHelper"
        try:
            conn = self._get_connection()
            if method == "callHypiumApi":
                return conn.send_message(
                    {
                        "module": module,
                        "method": method,
                        "params": {
                            "api": f"Driver.{api}",
                            "this": self._driver_name,
                            "args": args,
                            "message_type": "hypium",
                        },
                    }
                )
            return conn.send_message(
                {
                    "module": module,
                    "method": method,
                    "params": {"api": api, "args": args},
                }
            )
        except TimeoutError:
            if not self._tried_starting:
                self._tried_starting = True
                self.stop()
                return self._send(method, api, args)
            raise

    def _get_connection(self) -> _RpcConnection:
        with self._conn_lock:
            if self._connection is None:
                self.start()
                conn = _RpcConnection()
                conn.set_on_message(lambda sid, msg: self.emit("message", sid, msg))
                conn.connect(self._port)
                self._pump_thread = threading.Thread(
                    target=conn.pump, name="hdctool-uitest-rpc", daemon=True
                )
                self._pump_thread.start()
                create_result = conn.send_message(
                    {
                        "module": "com.ohos.devicetest.hypiumApiHelper",
                        "method": "callHypiumApi",
                        "params": {
                            "api": "Driver.create",
                            "this": None,
                            "args": [],
                            "message_type": "hypium",
                        },
                    },
                    timeout=1.0,
                )
                self._driver_name = str(create_result["result"])
                self._connection = conn
            return self._connection

    def _forward_tcp(self, p: int) -> int:
        remote = f"tcp:{p}"
        forwards = self._target.list_forwards()
        for f in forwards:
            if f["remote"] == remote:
                return int(f["local"].replace("tcp:", ""))
        port = _sync_free_port()
        local = f"tcp:{port}"
        self._target.forward(local, remote)
        return port

    def _should_update_sdk(self) -> bool:
        result = self._shell(f"cat {AGENT_PATH} | grep -a UITEST_AGENT_LIBRARY")
        if "UITEST_AGENT_LIBRARY" not in result:
            return True
        ver = _get_sdk_version(result)
        return _cmp_version(ver, self._sdk_version) < 0

    def _update_sdk(self) -> None:
        self._shell(f"rm {AGENT_PATH}")
        self._target.send_file(str(self._sdk_path), AGENT_PATH)

    def _shell(self, command: str) -> str:
        conn = self._target.shell(command)
        data = conn.read_all()
        conn.end()
        return data.decode("utf-8", errors="replace")


def _get_sdk_version(raw: str) -> str:
    i = raw.find("@v")
    if i < 0:
        return "0"
    return raw[i + 2 :].strip()
