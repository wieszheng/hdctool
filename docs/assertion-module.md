# Assertion 断言模块

提供类似 Hypium 的断言功能，支持断言失败后自动截屏。

## 基础使用

```python
ui = target.create_ui_driver()
assertion = ui.assertion

# 断言相等
assertion.equal(1, 1)
assertion.equal("hello", "hello")

# 断言条件
assertion.is_true(True)
assertion.is_false(False)
assertion.is_none(None)
assertion.is_not_none("value")
```

## 断言失败时自动截屏

断言失败时会自动截取设备屏幕并保存到 `/tmp/assert_fail_<timestamp>.png`。

```python
# 获取最后一次失败的截图路径
path = assertion.last_screenshot_path

# 禁用失败截屏
assertion.enable_screenshot_on_fail(False)
```

## 相等性断言

### equal / not_equal

```python
# 断言相等
assertion.equal(10, 10)
assertion.equal("hello", "hello")
assertion.equal([1, 2], [1, 2])

# 断言不相等
assertion.not_equal(1, 2)
assertion.not_equal("hello", "world")
```

### is_true / is_false

```python
assertion.is_true(value == expected)
assertion.is_false(value == unexpected)
```

### is_none / is_not_none

```python
assertion.is_none(result)
assertion.is_not_none(data)
```

## 字符串断言

### contains / not_contains

```python
# 断言包含子串
assertion.contains("hello world", "world")
assertion.contains("hello world", "hello")

# 断言不包含子串
assertion.not_contains("hello world", "foo")
```

### starts_with / ends_with

```python
assertion.starts_with("hello world", "hello")
assertion.ends_with("hello world", "world")
```

### match_regexp

```python
# 断言匹配正则表达式
assertion.match_regexp("abc123", r"^\w+\d+$")
assertion.match_regexp("192.168.1.1", r"\d+\.\d+\.\d+\.\d+")
```

### length_equal

```python
assertion.length_equal("hello", 5)
assertion.length_equal([1, 2, 3], 3)
```

## 数值断言

### greater / greater_equal

```python
# 断言大于
assertion.greater(10, 5)

# 断言大于等于
assertion.greater_equal(10, 10)
assertion.greater_equal(10, 5)
```

### less / less_equal

```python
# 断言小于
assertion.less(5, 10)

# 断言小于等于
assertion.less_equal(10, 10)
assertion.less_equal(5, 10)
```

### in_range

```python
# 断言值在范围内
assertion.in_range(50, 0, 100)  # 50 在 [0, 100] 范围内
```

## 自定义失败消息

```python
assertion.equal(
    actual=actual_value,
    expect=expected_value,
    fail_msg=f"用户 {username} 的积分应为 {expected}，实际为 {actual}"
)
```

## 与 UI 结合使用

```python
from hdctool import create_client

client = create_client()
target = client.get_target(client.list_targets()[0])
ui = target.create_ui_driver()
assertion = ui.assertion

try:
    # 启动应用
    ui.app_manager.start_app("com.example.app")
    ui.wait_for_idle()

    # 获取屏幕信息
    size = ui.screen.get_display_size()
    
    # 断言
    assertion.greater(size["width"], 0, "屏幕宽度应大于 0")
    assertion.less(size["width"], 10000, "屏幕宽度应合理")
    
    # 导出布局
    layout = ui.dump_layout_json()
    
    # 断言布局结构
    assertion.is_not_none(layout, "布局不应为空")
    assertion.equal(layout.get("type"), "root", "根节点类型应正确")
    
finally:
    ui.stop()
```

## 与 CV 图像识别结合

```python
cv = ui.cv
assertion = ui.assertion

try:
    # 等待目标出现
    result = cv.wait_for_image("success_icon.png", timeout=10)
    
    # 断言图像存在
    assertion.is_not_none(result, "成功图标应出现")
    
    if result:
        # 断言匹配度足够高
        assertion.greater(result.confidence, 0.8, "匹配置信度应足够高")
        
        # 点击确认
        cv.find_and_click("confirm_button.png")
        
finally:
    ui.stop()
```

## 完整测试示例

```python
import hdctool

def test_app_launch():
    client = hdctool.create_client()
    target = client.get_target(client.list_targets()[0])
    ui = target.create_ui_driver()
    assertion = ui.assertion

    try:
        # 启动应用
        ui.app_manager.force_stop("com.example.app")
        ui.app_manager.start_app("com.example.app")
        ui.wait_for_idle()

        # 验证应用已启动
        result = ui.dump_layout_json()
        assertion.is_not_none(result, "布局应不为空")

        # 验证屏幕尺寸合理
        size = ui.screen.get_display_size()
        assertion.greater(size["width"], 0)
        assertion.greater(size["height"], 0)

        # 验证主界面元素
        texts = ui.cv.find_text("主页面")
        assertion.greater(len(texts), 0, "应显示主页面文字")

        print("所有断言通过!")

    finally:
        ui.stop()

if __name__ == "__main__":
    test_app_launch()
```
