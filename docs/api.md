# API Reference & 操作指南

本指南并非简单的函数名陈列，而是以 **实际操作场景** 为切入点，带你掌握 `hdctool` 各个核心能力的使用姿势。

---

## 1. 建立全局与设备连接 (Client & Target)

首先任何操作都要从连接开始。`hdctool` 是以全局 `Client` 管理多台设备并分配派生出独享的 `Target`。

### 1.1 初始化及多设备读取
```python
import hdctool

# 建立一个 Client 实例；会自动检测本地默认的 tcp:8710 hdc 进程
client = hdctool.create_client(connect_timeout=30.0)

# 获取所有设备的列表
targets = client.list_targets()
for connect_key in targets:
    # 拿到具体的底层 Target 句柄
    target = client.get_target(connect_key)
    # 取值进行验证与鉴别
    params = target.get_parameters()
    print(f"识别到设备: {connect_key} ({params.get('const.product.model')})")
```

### 1.2 动态监听设备上下线事件 (Tracker)
若是需要在后台自动化运维系统中监听设备的插拔，你可以使用内置的 `Tracker` 事件监听模型（基于 `EventEmitter`）。

```python
tracker = client.track_targets()

# 绑定设备插入及拔除事件
def on_add(key):
    print(f"新设备接入了: {key}")

def on_remove(key):
    print(f"设备断开了连接: {key}")

tracker.on("add", on_add)
tracker.on("remove", on_remove)

# 监听将在后台线程维持；可以通过手动调用停止
# tracker.end()
```

---

## 2. 操作底层设备 (Target)

当你通过 `client.get_target(key)` 获取设备句柄后，你可以避开传统缓慢的 CLI 进程调用，直接使用长连接发起操作。

### 2.1 高级原生 Shell 与短时回显
如果只是简单调用（比如通过 `param get` 或者短执行指令），可以使用 `hdc_shell`；如果有可能产生巨大日志并需要阻塞与主动停止的，推荐使用原生协议层封装的长连接 `shell()`。

```python
# 方案 A：快速拿短结果，等同跑了 `hdc -t key shell "whoami"`
who = target.hdc_shell("whoami")

# 方案 B：长连接通信
# 这是建立起一条 TCP 全双工通道后的交互，适合长耗时操作
conn = target.shell("ls -la /data/local/tmp")
try:
    # 阻塞读取全部数据
    data: bytes = conn.read_all()
    print(data.decode("utf-8"))
finally:
    # 确保关闭连接
    conn.end()
```

### 2.2 文件上行与下行、端口代理
无需调用 hdc CLI 的纯正 TCP 内部数据通信。

```python
# 将本地的安装包推送到远端设备的 tmp 目录
target.send_file(local="./app-debug.hap", remote="/data/local/tmp/app.hap")

# 拉取设备的截图（假设通过别的方式截图了）
target.recv_file(remote="/data/local/tmp/shot.png", local="./local_shot.png")

# 在鸿蒙设备的 UI 测试等场景中极其重要的端口转发
# 比如代理远端应用的 HTTP 调试口到本地的 8080
target.forward(local="tcp:8080", remote="tcp:80")
print(target.list_forwards())

# 解除绑定
target.remove_forward("tcp:8080", "tcp:80")
```

---

## 3. 鸿蒙界面自动化 (UiDriver 实践教程)

一旦调用 `target.create_ui_driver()`，脚本不仅会自动拉起设备上的 `uitest` 后台常驻进程，并且会自动进行 TCP 内部端口的自动暴露与对接代理！

> **前置提示**：`UiDriver` 必须在使用完毕时手动 `stop()`。

### 3.1 极简拉起与布局剖析
最常见的通过截取解析全屏幕结构树（XML 格式），转变为可以立刻用于提取与检索判断的字典格式：

```python
ui = target.create_ui_driver()
try:
    # 让设备立刻强制亮屏且解除锁屏控制（模拟人眼）
    if not ui.screen.is_display_on():
        ui.screen.wake_up()
    ui.screen.unlock()
    
    # 拉起一个想测试的应用包
    ui.app_manager.start_app("com.example.app")

    # [核心用法] - 拉取当前全屏所有 UI 的节点属性和归属关系字典
    # 并且可以在指定路径保存一份便于调试的快照文件
    layout: dict = ui.dump_layout_json(file_path="current_ui.json")
    print(f"当前界面的根节点名称是: {layout.get('type')}")
    
finally:
    # 【非常重要】结束一定要停掉后台驱动进程！
    ui.stop()
```

### 3.2 模拟人的物理操作行为
直接使用抽象良好的按键模拟子系统：

```python
# 1. 基础点触点击操作
ui.uinput.tap(x=500, y=500)     # Input驱动的低维层模拟
ui.gestures.click(500, 500)     # 手势驱动的模拟，可以做一些稍微高级的状态追踪

# 2. 从屏幕底部滑动到顶部以滚动列表 (x1, y1) -> (x2, y2) 耗时 500ms
size = ui.screen.get_display_size()
center_x = size["width"] // 2
ui.gestures.swipe(center_x, 1000, center_x, 200, duration_ms=500)

# 3. 更快速带有阻尼感的抛滑（Fling）
ui.gestures.fling(center_x, 1000, center_x, 200)

# 4. 系统按键组合注射
# 按下键盘物理 4 代表返回键 (Return/Back)
ui.uinput.key_event(4)
```

### 3.3 实时交互数据拉取 (Hilog 及录屏)
可以通过绑定的系统打通鸿蒙的 Logging 以及设备的实时显示器信息反馈。

```python
# 抓取不断输出的 Hilog 信号流
def log_reader(entry):
    if "ERROR" in entry.message:
        print(f"捕获到红色故障日志: {entry.message}")

logger_process = ui.hilog.listen(log_reader)
# 后续想停下手可调用 logger_process.end()

# 获取设备画面的实时流 (例如用于机器视觉识别)
def frame_receiver(img_bytes: bytes):
    # 这里拿到的是实时帧，可以存入数据库也可以喂给识别模型
    pass

ui.screen.start_capture_screen(frame_receiver)
```

---

## 4. 机器视觉与断言组合利器

结合刚刚整理的测试包，`hdctool` 将测试能力升级至不仅依赖 DOM 节点，也支持依赖直观的图像校验来确认应用表现。

### 4.1 智能截图留证 (Assertion)
在测试脚本中大量替代基础的 python `assert` 逻辑，能够自动为你记录下“死前一帧”。

```python
assertion = ui.assertion
assertion.enable_screenshot_on_fail(True)  # 默认开启截屏机制

try:
    layout = ui.dump_layout_json()
    # 当找不到指定条件就会在 /tmp 目录下（或配置指定的目录）生成一张现场图！
    assertion.is_not_none(layout, "【灾难】整个鸿蒙 UI 树塌毁丢失了！")
    
    # 对于业务数据的断言更为灵活 (它本身也内置了深层比较功能)
    assertion.greater(100, 50, "必须大于50")
    assertion.match_regexp("13800138000", r"^1\d{10}$")
except Exception as err:
    print(f"验证已阵亡，截图留存于: {assertion.last_screenshot_path}")
```

### 4.2 OpenCV 无标记点按压 (CV 模块)
不必依赖控件节点树，直接采用截图对比大法找按钮（此用法需要保证环境中已安装 OpenCV 支持）。

```python
cv = ui.cv

# 如果目标没有出现就一直死等阻塞最多 15 秒！
if cv.wait_for_image("submit_btn_template.png", timeout=15):
    # 图标加载完毕，立刻获取它在页面中所在区域的置信中心点并完成点击
    cv.find_and_click("submit_btn_template.png", threshold=0.85)

# (选修)：配合 PaddleOCR 直接不靠 XML 解析提取非标准 UI 的文字
texts = cv.ocr_text()
for item in texts:
    print(f"发现文字: '{item['text']}' 置信度达: {item['confidence']}")
```
