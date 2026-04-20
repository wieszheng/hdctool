# UiDriver 指南

UiDriver 是 `hdctool` 提供的 UI 自动化模块，基于 OpenHarmony/HarmonyOS 的 Hypium/uitest 框架。

## 创建 UiDriver

```python
from hdctool import create_client

client = create_client()
target = client.get_target(client.list_targets()[0])

# 创建 UI 自动化实例
ui = target.create_ui_driver()

try:
    # 使用 UI 功能...
finally:
    ui.stop()  # 退出时必须停止
```

## 子模块

UiDriver 提供多个子系统模块：

| 模块 | 用途 | 访问方式 |
|------|------|----------|
| screen | 屏幕控制 | `ui.screen` |
| gestures | 手势操作 | `ui.gestures` |
| app_manager | 应用管理 | `ui.app_manager` |
| storage | 文件存储 | `ui.storage` |
| system | 系统操作 | `ui.system` |
| uinput | 键值注入 | `ui.uinput` |
| hilog | 日志桥接 | `ui.hilog` |
| cv | 图像识别 | `ui.cv` |
| assertion | 断言模块 | `ui.assertion` |

## 屏幕操作

```python
# 获取屏幕尺寸
size = ui.screen.get_display_size()
width, height = size["width"], size["height"]

# 屏幕控制
ui.screen.wake_up()      # 唤醒屏幕
ui.screen.unlock()       # 解锁
ui.screen.set_orientation("portrait")  # 设置方向

# 截屏
ui.screen.start_capture_screen(callback)  # 流式截屏
ui.screen.stop_capture_screen()

# 布局导出
layout = ui.dump_layout_json()  # 返回 dict
xml = ui.dump_layout()  # 返回 XML 字符串
```

## 手势操作

```python
# 点击
ui.gestures.click(500, 500)
ui.uinput.tap(500, 500)

# 长按
ui.gestures.long_click(500, 500, 1500)  # 1500ms

# 滑动
ui.gestures.swipe(100, 500, 400, 500, 300)  # 从 (100,500) 滑到 (400,500)

# 拖拽
ui.gestures.drag((100, 500), (400, 500), 500)

# 抛掷
ui.gestures.fling((100, 500), (400, 800))

# 双指缩放
ui.gestures.pinch((500, 500), 1.5)  # 放大 1.5 倍
```

## 应用管理

```python
# 启动应用
ui.app_manager.start_app("com.example.myapp")

# 停止应用
ui.app_manager.force_stop("com.example.myapp")

# 清除应用数据
ui.app_manager.clear_app_data("com.example.myapp")

# 获取应用信息
info = ui.app_manager.get_bundle_info("com.example.myapp")

# 列出已安装包
packages = ui.app_manager.list_packages()
```

## 文件存储

```python
# 推送文件到设备
ui.storage.push_file("local/app.hap", "/data/local/tmp/app.hap")

# 拉取设备文件
ui.storage.pull_file("/data/local/tmp/screenshot.png", "local.png")

# 检查文件是否存在
exists = ui.storage.has_file("/data/local/tmp/app.hap")

# 删除文件
ui.storage.rm_file("/data/local/tmp/app.hap")
```

## 键值注入

```python
# 点击
ui.uinput.tap(500, 500)

# 按键事件
ui.uinput.key_event(4)  # 返回键
ui.uinput.key_event(3)  # Home 键

# 按键组合
ui.uinput.key_combo(25, 4)  # Ctrl+C 等组合键

# 鼠标操作
ui.uinput.mouse_click(500, 500)
ui.uinput.mouse_move(600, 600)
```

## 等待空闲

```python
# 等待设备空闲
ui.wait_for_idle(idle_time=100, timeout=5000)
```

## RPC 扩展

```python
# 调用 Driver API
result = ui.call_driver("getCurrentFocus", [])

# 调用其他 RPC 方法
result = ui.call_rpc("DeviceInfo", "getDeviceInfo", {})
```
