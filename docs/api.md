# API 参考指南

本章节提供了 `hdctool` 的核心类及核心模块的方法参考。

## 核心底层对象

### hdctool.create_client
`create_client(host="127.0.0.1", port=8710, bin="hdc", connect_timeout=30.0, read_timeout=None, hdc_subprocess_timeout=120.0) -> Client`

快速创建并返回一个全局的 HDC 客户端实例。

### Client (全局客户端)
- `list_targets() -> list[str]`：返回当前所有已连接设备的 `connect_key` 列表。
- `track_targets() -> Tracker`：持续监听设备上下线事件。
- `get_target(connect_key: str) -> Target`：获取一个指定标识的 `Target` 设备操控实例。
- `hdc(args: list[str], timeout: float | None = None) -> str`：在宿主机执行全局纯 CLI 指令。
- `list_forwards()` / `list_reverses()`：查看当前的端口转发/反向端口规则。
- `kill()`：强杀后端的 `hdc` 守护进程。

### Target (单一设备代理)
- `hdc_shell(command: str) -> str`：单次极速调用 CLI 执行 `hdc shell <cmd>`。
- `get_parameters() -> dict`：通过 TCP 协议极速拉取设备的所有参数（等同 `param get`）。
- `shell(command: str) -> Connection`：通过 TCP 原生协议发起 Shell 交互会话，适合长连接监听或获取极大返回流。
- `send_file(local: str, remote: str)`：将本地文件推送到设备。
- `recv_file(remote: str, local: str)`：将设备文件拉取到本地。
- `install(hap: str)` / `uninstall(bundle_name: str)`：静默安装或卸载应用。
- `forward(local: str, remote: str)`：开启端口转发。
- `screenshot_to_local(local: str)`：原生截屏并回传。
- `open_hilog(clear=False) -> Hilog`：打开 hilog 的事件流读写器。
- `create_ui_driver(sdk_path=None) -> UiDriver`：在此设备上孵化并代理 `UiDriver` 进程，返回 UiDriver 实例管理器。

---

## UiDriver 自动化驱动

调用 `target.create_ui_driver()` 后产生的中心管理对象。  
必须使用完后调用 `.stop()` 否则由于长驻进程问题会导致内存或进程泄露。

**基础能力：**
- `start()` / `stop()`：手动启停 UiDriver 守护进程。
- `dump_layout()` / `dump_layout_json()`：拉取当前屏幕所有组件的层级树，并返回 XML 或 Dict。
- `get_display_size() -> dict`：返回屏幕宽高 `{"width": 720, "height": 1280}`。
- `call_driver(api: str, args: list) -> Any`：通过 RPC 透传调用设备端 `Hypium Driver.<api>` 的底层能力。

### UiDriver 内置子系统
UiDriver 初始化后已经自动挂载了以下高级抽象子系统，可以直接使用点前缀调用（例：`ui.screen.wake_up()`）：

#### 1. ui.screen (屏幕管理)
控制设备的背光、方向及抓取屏幕图像。
- `wake_up()` / `sleep()`：点亮与熄灭屏幕。
- `unlock()` / `lock()`：解开或锁定屏幕。
- `is_display_on()` / `is_display_locked()`：获取状态标识。
- `set_orientation(orientation: str|int)`：旋转屏幕到特定方向。
- `start_capture_screen(callback: Callable[[bytes], Any])`：注册视频流并实时以 bytes 回调每一帧图像，常用于图像识别与录制。
- `start_screen_record(remote_path)`：原生态的设备录屏。

#### 2. ui.gestures (手势操作)
负责常见的屏幕物理坐标触摸与手势行为。
- `click(x, y)` / `double_click(x, y)`：单双击屏幕对应位置。
- `long_click(x, y, duration_ms)`：长按坐标位置。
- `swipe(x1, y1, x2, y2, duration_ms)`：基础滑动。
- `drag(x1, y1, x2, y2)`：长按并拖拽（适用于可移除组件等）。
- `fling(x1, y1, x2, y2, velocity)`：自带抛掷加速滑行效果。
- `pinch(center_x, center_y, scale)`：双指缩放调整。

#### 3. ui.app_manager (应用及包管理)
掌管应用级和包管理生命周期。
- `start_app(bundle_name, ability_name=None)`：热启或冷拉起应用。
- `stop_app(bundle_name)` / `force_stop(bundle_name)`：关闭或强杀应用进程。
- `clear_app_data(bundle_name)` / `clear_app_cache(bundle_name)`：清理存储数据与缓存。
- `get_app_info(bundle_name) -> dict`：获取诸如版本号、包标识、权限等详情信息。
- `get_installed_apps() -> list[str]`：查阅所有已装应用的包名集合。

#### 4. ui.uinput (系统注入输入法)
基于最底层的信号下发生效，包括系统按键等。
- `key_event(keycode)`：单次注入特殊的 KeyCode （如物理返回键 4，电源键等）。
- `key_combo(*keycodes)`：并排或组合注入多个按键。
- `mouse_click(x, y)`：鼠标模式进行模拟操作。

#### 5. ui.system (系统辅助与参数)
一些基于 Shell 高度封装的检查器。
- `get_device_type()` / `get_device_model()` / `get_system_version()`：设备软硬件一览。
- `get_param(key)` / `set_param(key, value)`：更改系统设定档参数。
- `reboot()`：设备重启。

#### 6. ui.storage (内部存储 IO)
借用 hdc 代理的推拉能力简化操作。
- `push_file(local, remote)` / `pull_file(remote, local)`
- `has_file(remote_path)` / `rm_file(remote_path, recursive=False)`

#### 7. ui.hilog (设备日志系统)
与鸿蒙标准的 logging 系统打通。
- `open(clear=False) -> Hilog`：产生一个用于迭代的迭代器对象。
- `listen(on_entry)`：流式传输回调处理机制。

---

## 扩展能力模块

`UiDriver` 新近引入的能力，为了适配不同测试范式的特殊需求。

### 核心机器视觉解析 ui.cv (基于 OpenCV)
*注意：本系统需要额外安装 opencv 与 NumPy：`pip install hdctool[cv]`*  
负责利用基于图像的识别方案反向驱动和验证自动化流程。  
- `find_image(template)` / `find_images(template)`：用图像定位屏幕元素的坐标，支持自定义模板（甚至跨分辨率自适应匹配度计算）。
- `find_and_click(template)`：识别完毕后立即在画面区域的正中心点击。
- `wait_for_image(template, timeout)`：阻断等待某个动画或图标加载结束渲染出现。
- `ocr_text()` / `find_text(text)`：如果环境配有了 paddleocr，可以直接从非标准 UI 树的视图（例如 Canvas 或游戏层）提取文字并获取它的边界矩阵。
- `detect_colors()` / `get_pixel_color(x, y)`：专门用于处理界面变色或纯色判断，比如验证点赞心形的改变。

### 轻量级验证系统 ui.assertion (轻量级断言)
专为测试套件设计的验证链，内置错误截图能力以保留现场。
- **自动收集**：通过 `assertion.enable_screenshot_on_fail()` 当任意断言失败时能自动 `snapshot` 保留到指定的暂存档中。
- `equal()` / `is_true()` / `is_not_none()`：值域等一性比对（如果包含 dict 或 list ，内部将自动转化或深层比较）。
- `contains()` / `match_regexp()`：为正则与子字符串测试量身定做。
- `greater()` / `less()` / `in_range()`：极佳契合页面布局尺寸边界计算及位置比对的范围验证函数。
