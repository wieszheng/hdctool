# hdctool

Python 实现的 **HDC（Harmony Device Connector）** 同步客户端，用于列举设备、Shell、端口转发、安装包、**UiDriver（Hypium/uitest）** 等。

## 安装

```bash
pip install -e .
```

开发依赖：`pip install -e ".[dev]"`

## 用法

```python
import hdctool

client = hdctool.create_client()
for key in client.list_targets():
    t = client.get_target(key)
    print(t.get_parameters().get("const.product.name"))
```

### 纯 HDC（子进程，不经由 TCP 会话）

适合简单 `shell`、与现有 `Target.shell`（长连接）互补：

```python
out = t.hdc_shell("param get const.product.name")
raw = t.hdc(["shell", "whoami"])
```

不带 `-t` 的全局命令：

```python
client.hdc(["list", "targets"])
```

### 超时与异常

`create_client` 支持关键字参数：

- `connect_timeout`：连接本机 HDC 端口超时（秒，默认 `30`）
- `read_timeout`：已连接套接字读超时；`None` 表示阻塞（默认 `None`，适合大体积 shell 输出）
- `hdc_subprocess_timeout`：`hdc` CLI 子进程默认超时（默认 `120`，可为 `None` 表示不设限）

失败时可能抛出 `hdctool.HdcTcpError`、`HdcHandshakeError`、`HdcSubprocessError` 等，异常对象带 `context` 字典便于记录。

### 日志

设置环境变量 `HDCTOOL_LOG_LEVEL=DEBUG`（或 `INFO` 等）后，包内使用 `logging.getLogger("hdctool")` 的日志会按级别输出；也可在代码中调用 `hdctool.configure_logging()`。

### UiDriver 子系统

`UiDriver` 提供属性：`gestures`、`app_manager`、`screen`、`storage`、`system`、`hilog`、`uinput`（手势/键鼠/表冠、应用与包信息、亮灭屏与录屏、文件 push/pull、系统参数、hilog 监听、按键注入等）。未封装的设备侧能力可用 `call_driver` / `call_rpc`。实现见 `src/hdctool/ui/subsystems.py`。

示例脚本见 `examples/hdc_demo.py`。

## 布局（src）

- `src/hdctool/` — 包根，`py.typed` 标明支持类型检查
- `src/hdctool/uitestkit_sdk/` — uitest agent（`uitest_agent_*.so`）随仓库提交，供 `UiDriver` 推送到设备；若克隆后缺失请从本地 Harmony/OpenHarmony uitest 工具链拷贝同名文件
- `examples/` — 可运行示例
- `tests/` — pytest
- `.github/workflows/ci.yml` — CI（Ruff + pytest，Ubuntu / Windows × Python 3.10–3.12）

## 版本与变更

`hdctool.__version__` 与 `pyproject.toml` 中 `[project].version` 一致。用户可见变更见根目录 `CHANGELOG.md`。维护者发布流程见 `RELEASING.md`。
