# hdctool

[![PyPI version](https://img.shields.io/pypi/v/hdctool.svg)](https://pypi.org/project/hdctool/)
[![Python version](https://img.shields.io/pypi/pyversions/hdctool.svg)](https://pypi.org/project/hdctool/)
[![License](https://img.shields.io/github/license/wieszheng/hdctool.svg)](https://github.com/wieszheng/hdctool/blob/main/LICENSE)
[![CI Status](https://github.com/wieszheng/hdctool/actions/workflows/ci.yml/badge.svg)](https://github.com/wieszheng/hdctool/actions)

**hdctool** 是一个功能强大且类型安全（Typed）的 Python 客户端，专为 **[HDC (Harmony Device Connector / OpenHarmony 设备连接器)](https://gitee.com/openharmony/developtools_hdc)** 设计。

它不仅支持以传统的命令行（CLI）流式调用 HDC 指令，更原生实现了 **HDC 守护进程的 TCP 直接通信**，能以更高效的长连接方式实现设备列举、Shell 互操作、端口转发、文件传输以及完整的设备级 UI 自动化测试控制。

---

## 🚀 核心特性

- **协议级直连**：部分核心操作（如 Shell 通信、端口转发、获取参数）跨过 `hdc` CLI 进程直接通过 TCP 与 HDC 服务端交互，执行超快，避免进程起停开销。
- **设备生命周期管理**：提供稳定的一体化接口实现对特定设别（`Target`）的各类操作。
- **UiDriver 原生内嵌**：内置 `uitestkit_sdk`，对 OpenHarmony/HarmonyOS 的 UI 测试套件（Hypium/uitest）进行了高度封装。可在 Python 端用极简代码拉起应用、触发点击滑动、解析 UI 树、监听 hilog。
- **类型完善**：`py.typed` 完整支持，所有暴露的 API 皆有 MyPy / Pylance 类型提示，极大地提升了开发体验。

---

## 📦 安装

推荐使用 `pip` 进行安装：

```bash
pip install hdctool
```

如果你想要克隆代码进行本地开发：

```bash
git clone https://github.com/wieszheng/hdctool.git
cd hdctool
pip install -e ".[dev]"
```

---

## 📖 快速上手

### 1. 基础连接与拉取设备信息

```python
import hdctool

# 创建全局 HDC 客户端
client = hdctool.create_client()

# 列出当前连接的所有设备的 connect key (如 sn 码 或 IP)
targets = client.list_targets()

if targets:
    # 绑定到首个设备
    target = client.get_target(targets[0])
    
    # 协议级获取设备属性字典
    params = target.get_parameters()
    print("设备名称:", params.get("const.product.name"))
    print("系统版本:", params.get("const.product.software.version"))
```

### 2. Shell 互操作与原生命令

`hdctool` 允许你以多种方式下行命令到设备设备中：

```python
# 纯 CLI 调用 (适合一次性结果回调、需要拉起 hdc 子进程)
output = target.hdc_shell("param get const.product.name")
print("CLI Shell 响应:", output)

# 全局原生纯 CLI 调用 (如 `hdc list targets`)
client.hdc(["list", "targets"])

# TCP 长连接直接 Shell (适合大型或交互式流)
conn = target.shell("whoami")
print("TCP Shell 响应:", conn.read_all().decode())
conn.end()
```

### 3. 应用操作与文件传输

```python
# 文件拉取与推送
target.recv_file("/data/local/tmp/test.txt", "local_test.txt")
target.send_file("local_test.txt", "/data/local/tmp/test2.txt")

# 静默安装与卸载应用包 (hap)
target.install("/path/to/app.hap")
target.uninstall("com.example.myapp")

# 端口转发控制 (local -> remote)
target.forward("tcp:8080", "tcp:80")
print(target.list_forwards())
target.remove_forward("tcp:8080", "tcp:80")
```

---

## 🤖 UiDriver — UI 自动化测试模块

对于在 HarmonyOS / OpenHarmony 系统上的脱机自动化脚本或端到端测试，`hdctool` 提供了原生的 `UiDriver` 支持，它通过底层的 RPC 为你扫平了手写繁重 shell 的烦恼。

```python
# 从 target 实例化，它会自动将正确的 agent.so 推送到设备并拉起 ui 进程
ui = target.create_ui_driver()

try:
    # 亮屏及解锁判断
    if not ui.screen.is_display_on():
        ui.screen.wake_up()
    ui.screen.unlock()

    # 应用管理与拉起
    ui.app_manager.force_stop("com.baidu.yiyan")
    ui.app_manager.start_app("com.baidu.yiyan")

    # 设备手势与键位控制
    width, height = ui.screen.get_display_size().values()
    ui.gestures.touch_down(width // 2, height // 2)
    ui.gestures.touch_up(width // 2, height // 2)
    
    ui.uinput.tap(500, 500)
    ui.uinput.key_event(4)  # KeyCode 4 为返回键
    
    # 解析当前画面的 UI Tree (返回解析好的字典或原始 XML)
    layout_json = ui.dump_layout_json("current_layout.json")
    print(layout_json)
    
    # 截屏操作并接收数据流回调
    def on_frame(data: bytes):
        with open("screenshot.jpg", "wb") as f:
            f.write(data)
            
    ui.screen.start_capture_screen(on_frame)
    
finally:
    # 退出前一定要停掉服务代理进程
    ui.stop()
```

### UiDriver 内置子系统模块速览

| 子模块属性 | 概述 | 常见 API |
| --- | --- | --- |
| `ui.screen` | 屏幕状态与控制 | `wake_up()`, `unlock()`, `dump_layout()`, `start_capture_screen()` |
| `ui.gestures` | 手势控制 | `click()`, `swipe()`, `drag()`, `pinch()`, `mouse_click()` |
| `ui.app_manager` | 应用管理器 | `start_app()`, `stop_app()`, `clear_app_data()`, `get_app_version()` |
| `ui.storage` | 设备存储中心 | `push_file()`, `pull_file()`, `has_file()`, `rm_file()` |
| `ui.system` | 系统辅助与参数 | `get_device_type()`, `get_api_level()`, `reboot()` |
| `ui.uinput` | 输入相关底层 | `tap()`, `key_event()`, `key_combo()`, `inject_key()` |
| `ui.hilog` | 日志桥接 | `open()`, `listen()` |

如果遇到框架尚未内置的 Hypium RPC 能力，可直接通过 `ui.call_driver(api_name, args)` 和 `ui.call_rpc(method, api, args)` 反射调用。

*更多用例演示可参考仓库内的 [`examples/hdc_demo.py`](./examples/hdc_demo.py) 文件。*

---

## ⚙️ 超时与错误处理

通过在客户端建立连接时，你可以按需自定义所有涉及到阻塞的设定：

```python
client = hdctool.create_client(
    connect_timeout=30.0,            # 连接本机 HDC Daemon 的超时(秒)
    read_timeout=None,               # 已连接 Socket 读超时(秒) - None 适合等待大型输出
    hdc_subprocess_timeout=120.0     # hdc CLI 子进程的最长生命周期(秒)
)
```

在执行出错时，程序将基于错误类型抛出异常体系 `hdctool.HdcException`（具体如 `HdcTcpError`, `HdcSubprocessError` 等）。捕获 `HdcSubprocessError` 时可利用其实例所携带的 `context` 字典获取故障的详细标准输出以方便诊断。

若需开启内部调试日志：
```bash
export HDCTOOL_LOG_LEVEL=DEBUG
```
或通过代码直接配置 `hdctool.configure_logging()`。

---

## 📋 维护与开发

关于版本的规范、CI 工作流以及发布到 PyPI 的指引，请参考维护者专用文档：[RELEASING.md](./RELEASING.md)。

## 📄 协议

本项目基于 **MIT License** 开源。详细条款请参见 `LICENSE`。
