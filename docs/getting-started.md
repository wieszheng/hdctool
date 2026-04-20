# 快速开始

## 安装

```bash
pip install hdctool
```

可选依赖：
```bash
# OpenCV 图像识别
pip install hdctool[cv]

# 开发依赖
pip install hdctool[dev]
```

## 基本使用

```python
import hdctool

# 创建 HDC 客户端
client = hdctool.create_client()

# 获取设备列表
targets = client.list_targets()

if targets:
    # 绑定设备
    target = client.get_target(targets[0])

    # 获取设备参数
    params = target.get_parameters()
    print(params.get("const.product.name"))

    # 文件传输
    target.send_file("local.txt", "/data/local/tmp/remote.txt")
    target.recv_file("/data/local/tmp/remote.txt", "local.txt")

    # Shell 命令
    output = target.hdc_shell("ls /data/local/tmp")

    # UI 自动化
    ui = target.create_ui_driver()
    try:
        ui.screen.wake_up()
        ui.app_manager.start_app("com.example.app")
        ui.click(500, 500)
    finally:
        ui.stop()
```

## 下一步

- [UiDriver 指南](./ui-driver.md) - 完整的 UI 自动化使用
- [CV 图像识别](./cv-module.md) - 图像匹配与 OCR
- [Assertion 断言](./assertion-module.md) - 自动化测试断言
