# 变更记录

本文档遵循用户可见行为变更的简要记录；版本号与 `pyproject.toml`、`hdctool.__version__` 保持一致。

## 0.4.2（2026-04-19）

### 变更

- 默认 uitest agent 升级为 **`uitest_agent_v1.2.2.so`**（`SDK_VERSION_DEFAULT` = `1.2.2`）。请将对应二进制置于 `src/hdctool/uitestkit_sdk/` 并提交。

## 0.4.1（2026-04-19）

### 变更

- **版本库**：不再通过 `.gitignore` 排除 `*.so`，`src/hdctool/uitestkit_sdk/` 下的 `uitest_agent_*.so` 可正常纳入 Git 与发行包。
- **元数据**：`pyproject.toml` 中项目主页、仓库与 Issues 链接改为 [wieszheng/hdctool](https://github.com/wieszheng/hdctool)。

## 0.4.0（2026-04-19）

### 新增

- **UiDriver 子系统属性**：`gestures`、`app_manager`、`screen`、`storage`、`system`、`hilog`、`uinput`（见 `ui/subsystems.py`）。
- **手势与键鼠**：`drag` / `fling` / `pinch`、鼠标移动/点击/右键/双击/滚轮、表冠 `crown_rotate`（多 API 名回退）。
- **应用**：`install_app` / `uninstall_app` / `clear_app_data` / `force_stop` / `get_bundle_info` / `list_packages` / `running_processes`。
- **文件**：`storage.push_file` / `pull_file` / `has_file` / `rm_file`。
- **屏幕与电源**：亮灭屏、电源键、`lock`/`unlock`、`set_orientation`、`set_screen_off_timeout_ms`、录屏起停（Hypium Driver）、截屏流复用现有 Captures。
- **扩展入口**：`UiDriver.call_driver`、`UiDriver.call_rpc` 便于对接未封装的设备侧 API。

## 0.3.0（2026-04-19）

### 新增

- **纯 HDC（CLI）**：`Client.hdc(args)` 不带 `-t`；`Target.hdc` / `Target.hdc_shell` 带 `-t`；`Target.screenshot_to_local`（`snapshot_display` + `file recv`）。
- **超时**：`Client` 支持 `connect_timeout`、`read_timeout`（TCP 会话）、`hdc_subprocess_timeout`（`hdc` 子进程与 `ExecCommand`）；`Client.kill` 支持 `timeout`（Windows `taskkill`）。
- **异常与日志**：`HdcToolError` / `HdcTcpError` / `HdcHandshakeError` / `HdcSubprocessError`；标准库 `logging` 命名空间 `hdctool`，环境变量 `HDCTOOL_LOG_LEVEL`（默认 `WARNING`）；`configure_logging` / `get_logger` 可从包根导入。
- **UiDriver**：`press_back`、`press_home`、`click`、`double_click`、`long_click`、`start_app`、`stop_app`、`swipe`（参数依赖设备侧 Hypium `Driver` RPC，若与固件不一致请按需调整）。

### 变更

- `file recv/send`、`install`/`uninstall` 失败时抛出 `HdcSubprocessError`（含 `returncode`、输出片段等上下文），不再使用裸 `RuntimeError`。
- TCP 连接失败、握手失败、读超时等映射为 `HdcTcpError` / `HdcHandshakeError`（`HdcTcpError` 亦为 `ConnectionError` 子类，便于与 `read_all` 等逻辑兼容）。

### 文档

- 新增 `RELEASING.md`：PyPI 发布流程说明。

## 0.2.0 及更早

见仓库历史与 `git log`（此前未维护本文件）。
