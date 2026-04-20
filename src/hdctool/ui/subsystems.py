"""UiDriver 子系统门面：在 ``UiDriver`` 上以属性挂载（app_manager、screen、storage 等）。

多数设备能力通过 Hypium ``Driver.<api>`` 或 uitest RPC 转发；具体 API 以设备/uitest_agent
版本为准，调用失败时请用 :meth:`UiDriver.call_driver` 对照设备侧文档调整参数。
"""

from __future__ import annotations

import json
import shlex
import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from ..hilog import Hilog, HilogEntry

if TYPE_CHECKING:
    from .driver import UiDriver


def _point(x: float, y: float) -> dict[str, float]:
    return {"x": x, "y": y}


class UiGestures:
    """点击、滑动、拖拽、惯性滑动、键鼠、表冠等（Hypium Driver + Gestures RPC）。"""

    def __init__(self, driver: UiDriver) -> None:
        self._d = driver

    def touch_down(self, x: float, y: float) -> None:
        self._d.touch_down(x, y)

    def touch_move(self, x: float, y: float) -> None:
        self._d.touch_move(x, y)

    def touch_up(self, x: float, y: float) -> None:
        self._d.touch_up(x, y)

    def click(self, x: float, y: float) -> None:
        self._d.click(x, y)

    def double_click(self, x: float, y: float) -> None:
        self._d.double_click(x, y)

    def long_click(self, x: float, y: float, duration_ms: int = 1500) -> None:
        self._d.long_click(x, y, duration_ms)

    def swipe(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        duration_ms: int = 300,
    ) -> None:
        self._d.swipe(x1, y1, x2, y2, duration_ms)

    def drag(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        duration_ms: int = 500,
    ) -> None:
        """拖拽（优先 ``Driver.drag``，不存在时退化为慢速 ``swipe``）。"""
        try:
            self._d.call_driver(
                "drag",
                [_point(x1, y1), _point(x2, y2), duration_ms],
            )
        except RuntimeError:
            self._d.swipe(x1, y1, x2, y2, max(duration_ms, 400))

    def fling(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        *,
        duration_ms: int = 200,
        velocity: float | None = None,
    ) -> None:
        """快速滑动 / fling；部分固件为 ``Driver.fling``。"""
        args: list[Any] = [_point(x1, y1), _point(x2, y2), duration_ms]
        if velocity is not None:
            args.append(velocity)
        self._d.call_driver("fling", args)

    def pinch(
        self,
        center_x: float,
        center_y: float,
        *,
        scale: float = 0.5,
        duration_ms: int = 400,
    ) -> None:
        self._d.call_driver(
            "pinch",
            [_point(center_x, center_y), scale, duration_ms],
        )

    def mouse_move(self, x: float, y: float) -> None:
        self._d.call_driver("mouseMoveTo", [_point(x, y)])

    def mouse_click(self, x: float, y: float, button: int = 0) -> None:
        self._d.call_driver("mouseClick", [_point(x, y), button])

    def mouse_right_click(self, x: float, y: float) -> None:
        self._d.call_driver("mouseRightClick", [_point(x, y)])

    def mouse_double_click(self, x: float, y: float) -> None:
        self._d.call_driver("mouseDoubleClick", [_point(x, y)])

    def mouse_scroll(self, dx: float, dy: float) -> None:
        self._d.call_driver("mouseScroll", [dx, dy])

    def mouse_scroll_at(self, x: float, y: float, dx: float, dy: float) -> None:
        self._d.call_driver("mouseScrollAt", [_point(x, y), dx, dy])

    def crown_rotate(self, delta: float, *, steps: int = 1) -> None:
        """穿戴设备表冠旋转（``Driver.rotateCrown`` / ``crownRotate`` 依固件二选一）。"""
        try:
            self._d.call_driver("rotateCrown", [delta, steps])
        except RuntimeError as e1:
            try:
                self._d.call_driver("crownRotate", [delta, steps])
            except RuntimeError as e2:
                raise RuntimeError(
                    f"rotateCrown failed: {e1!s}; crownRotate failed: {e2!s}"
                ) from e2


class UiAppManager:
    """应用生命周期、安装与包/进程信息。"""

    def __init__(self, driver: UiDriver) -> None:
        self._d = driver

    def start_app(
        self,
        bundle_name: str,
        ability_name: str | None = None,
        params: str = "",
    ) -> None:
        """启动应用

        Args:
            bundle_name: 应用包名
            ability_name: Ability 名称（可选，自动匹配）
            params: 启动参数（可选）
        """
        cmd = "aa start"
        if ability_name:
            cmd += f" -a {ability_name}"
        if params:
            cmd += f" {params}"
        cmd += f" -b {bundle_name}"

        output = self._d._shell(cmd)
        if "successfully" not in output.lower():
            raise RuntimeError(f"Failed to start app: {output}")

    def stop_app(self, bundle_name: str) -> None:
        """强制停止应用"""
        output = self._d._shell(f"aa force-stop {bundle_name}")
        if "successfully" not in output.lower():
            raise RuntimeError(f"Failed to stop app: {output}")

    def get_app_info(
        self,
        bundle_name: str,
    ) -> dict[str, Any]:
        """获取应用信息

        Args:
            bundle_name: 应用包名

        Returns:
            应用信息字典
        """
        cmd = f"bm dump -n {bundle_name}"
        output = self._d._shell(cmd)

        try:
            start = output.find("{")
            if start >= 0:
                json_str = output[start:]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass

        raise RuntimeError(f"Failed to get app info: {output}")

    def get_installed_apps(
        self,
    ) -> list[str]:
        """获取已安装应用列表

        Returns:
            已安装应用包名列表
        """
        cmd = "bm dump -a"
        output = self._d._shell(cmd)
        lines = output.strip().split("\n")

        apps = []
        for line in lines:
            line = line.strip()
            if line and ":" not in line:
                apps.append(line)

        return apps

    def install_app(self, hap_path: str) -> None:
        self._d.target.install(hap_path)

    def uninstall_app(self, bundle_name: str) -> None:
        self._d.target.uninstall(bundle_name)

    def force_stop(self, bundle_name: str) -> None:
        self._d._shell(f"aa force-stop {shlex.quote(bundle_name)}")

    def clear_app_data(self, bundle_name: str) -> None:
        """清除应用数据"""
        output = self._d._shell(f"bm clean -d -n {bundle_name}")
        if "error" in output.lower():
            raise RuntimeError(f"Failed to clear app data: {output}")

    def clear_app_cache(self, bundle_name: str) -> None:
        """清除应用缓存"""
        output = self._d._shell(f"bm clean -c -n {bundle_name}")
        if "error" in output.lower():
            raise RuntimeError(f"Failed to clear app cache: {output}")

    def get_app_version(self, bundle_name: str) -> str | None:
        """获取应用版本"""
        try:
            info = self.get_app_info(bundle_name)
            return info.get("versionName", "")
        except Exception:
            return None

    def get_bundle_info(self, bundle_name: str) -> str:
        return self._d._shell(f"bm dump -n {shlex.quote(bundle_name)}")

    def get_app_permissions(self, bundle_name: str) -> list[str]:
        """获取应用权限列表"""
        output = self.d._shell(f"bm dump -n {bundle_name} -p")
        permissions = []
        for line in output.split("\n"):
            line = line.strip()
            if line.startswith("permission:"):
                perm = line.replace("permission:", "").strip()
                permissions.append(perm)
        return permissions


class UiStorage:
    """设备侧文件：推送/拉取/存在性/删除（推送拉取走 HDC file send/recv）。"""

    def __init__(self, driver: UiDriver) -> None:
        self._d = driver

    def push_file(self, local: str, remote: str) -> None:
        self._d.target.send_file(local, remote)

    def pull_file(self, remote: str, local: str) -> None:
        self._d.target.recv_file(remote, local)

    def has_file(self, remote_path: str) -> bool:
        q = shlex.quote(remote_path)
        out = self._d._shell(f"test -e {q} && echo OK || echo NO")
        return "OK" in out.splitlines()[-1] if out else False

    def rm_file(self, remote_path: str, *, recursive: bool = False) -> None:
        q = shlex.quote(remote_path)
        if recursive:
            self._d._shell(f"rm -rf {q}")
        else:
            self._d._shell(f"rm -f {q}")


class UiScreen:
    """亮灭屏、锁屏、方向、休眠时间、截屏/录屏相关。"""

    def __init__(self, driver: UiDriver) -> None:
        self._d = driver

    def wake_up(self) -> None:
        """唤醒屏幕"""
        self._d._shell("power-shell wakeup")

    def sleep(self) -> None:
        """关闭屏幕"""
        self._d._shell("power-shell suspend")


    def lock(self) -> None:
        try:
            self._d.call_driver("lockScreen", [])
        except RuntimeError:
            self.press_power()

    def is_display_on(self) -> bool:
        """检查屏幕是否点亮"""
        output = self._d._shell("hidumper -s PowerManagerService -a '-a'")
        return "Current State: AWAKE" in output

    def is_display_locked(self) -> bool:
        """检查屏幕是否锁屏"""
        output = self._d._shell("hidumper -s ScreenlockService -a -all")
        for line in output.split("\n"):
            if "screenLocked" in line:
                return "false" not in line
        return not self.is_display_on()

    def unlock(self) -> None:
        """解锁屏幕"""
        if not self.is_display_on():
            self.wake_up()
            time.sleep(1)

        size = self.get_display_size()
        cx = size["width"] // 2
        self._d.swipe(cx, int(size["height"] * 0.6), cx, int(size["height"] * 0.3), duration_ms=100)

    def set_orientation(self, orientation: int | str) -> None:
        """屏幕方向：整数（0–3）或 ``portrait`` / ``landscape`` 等字符串。"""
        if isinstance(orientation, str):
            self._d.call_driver("setDisplayOrientation", [orientation])
        else:
            self._d.call_driver("setDisplayOrientation", [orientation])

    def set_screen_off_timeout_ms(self, ms: int) -> None:
        self._d._shell(f"settings put system screen_off_timeout {int(ms)}")

    def get_display_size(self) -> Any:
        return self._d.get_display_size()

    def capture_layout(self) -> Any:
        return self._d.capture_layout()

    def start_capture_screen(
        self,
        callback: Callable[[bytes], Any],
        *,
        scale: float = 1,
    ) -> None:
        self._d.start_capture_screen(callback, scale=scale)

    def stop_capture_screen(self) -> None:
        self._d.stop_capture_screen()

    def start_screen_record(self, remote_path: str, **options: Any) -> None:
        """开始录屏（设备路径）。具体 RPC 名依 uitest 版本可能为 ``startScreenRecord`` 等。"""
        args: list[Any] = [remote_path]
        if options:
            args.append(options)
        self._d.call_driver("startScreenRecord", args)

    def stop_screen_record(self) -> None:
        self._d.call_driver("stopScreenRecord", [])


class UiSystem:
    """系统参数、版本信息等（以 shell 为主，必要时可配合 ``call_driver``）。"""

    def __init__(self, driver: UiDriver) -> None:
        self._d = driver

    def get_device_type(self) -> str:
        """获取设备类型"""
        return self._d._shell("param get const.product.devicetype").strip()

    def get_device_sn(self) -> str:
        """获取设备序列号"""
        return self._d.target.connect_key

    def get_device_model(self) -> str:
        """获取设备型号"""
        return self._d._shell("param get const.product.model").strip()

    def get_api_level(self) -> str:
        """获取 API 版本"""
        return self._d._shell("param get const.ohos.apiversion").strip()

    def get_system_version(self) -> str:
        """获取系统版本"""
        return self._d._shell("param get const.product.software.version").strip()

    def get_param(self, key: str) -> str:
        return self._d._shell(f"param get {key}").strip()

    def set_param(self, key: str, value: str) -> None:
        self._d._shell(f"param set {key} {value}")

    def reboot(self) -> None:
        self._d._shell("reboot")

    def uptime(self) -> str:
        return self._d._shell("uptime")


class UiHilogBridge:
    """与 ``Target.open_hilog`` 衔接；支持监听回调。"""

    def __init__(self, driver: UiDriver) -> None:
        self._d = driver

    def open(self, *, clear: bool = False) -> Hilog:
        return self._d.target.open_hilog(clear=clear)

    def listen(
        self,
        on_entry: Callable[[HilogEntry], None],
        *,
        clear: bool = False,
    ) -> Hilog:
        """打开 hilog 并在解析到新行时回调 ``on_entry``。

        调用方需对返回的 ``Hilog`` 执行 ``end()``。
        """
        h = self.open(clear=clear)
        h.on("entry", on_entry)
        return h


class UiUinput:
    """键值/按键注入等（Hypium Driver + ``input`` shell 回退）。"""

    def __init__(self, driver: UiDriver) -> None:
        self._d = driver

    def key_event(self, keycode: int) -> None:
        try:
            self._d.call_driver("pressKey", [keycode])
        except RuntimeError:
            self._d._shell(f"input keyevent {int(keycode)}")

    def key_combo(self, *keycodes: int) -> None:
        for k in keycodes:
            self.key_event(k)
            time.sleep(0.05)

    def inject_key(self, keycode: int) -> None:
        """与 ``key_event`` 相同别名。"""
        self.key_event(keycode)

    def tap(self, x: float, y: float) -> None:
        self._d.click(x, y)
