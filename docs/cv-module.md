# CV 图像识别模块

基于 OpenCV 的图像识别功能，支持模板匹配、OCR 文字识别等。

## 安装

```bash
pip install hdctool[cv]
# 或单独安装
pip install opencv-python numpy
```

## 基础使用

```python
ui = target.create_ui_driver()
cv = ui.cv
```

## 模板匹配

### 单匹配 find_image

在屏幕中查找单个模板位置：

```python
# 在当前屏幕中查找模板
result = cv.find_image("button.png")

if result:
    print(f"找到匹配，置信度: {result.confidence:.2%}")
    print(f"位置: {result.x}, {result.y}")
    print(f"中心点: {result.center.x}, {result.center.y}")
    print(f"边界: {result.bounds}")
else:
    print("未找到匹配")
```

**参数说明：**
- `template`: 模板图像路径或 numpy 数组
- `source`: 源图像，默认截取当前屏幕
- `threshold`: 匹配阈值，默认 0.8
- `region`: 搜索区域 `(x, y, width, height)`

### 多匹配 find_images

查找所有匹配位置：

```python
results = cv.find_images("icon.png", threshold=0.6, max_results=10)

for result in results:
    print(f"置信度: {result.confidence:.2%}, 位置: {result.center}")
```

### 匹配度计算 match_image

计算最佳匹配度（不返回位置）：

```python
similarity = cv.match_image("target.png")
print(f"匹配度: {similarity:.2%}")
```

## 查找并点击

```python
# 找到模板后自动点击中心点
success = cv.find_and_click("button.png")

# 指定自定义阈值
success = cv.find_and_click("button.png", threshold=0.9)
```

## 等待机制

### 等待图像出现

```python
# 等待最多 10 秒
result = cv.wait_for_image("loading.png", timeout=10, interval=0.5)

if result:
    print("图像出现了")
```

### 等待图像消失

```python
# 等待加载动画消失
disappeared = cv.wait_for_image_disappear("loading.png", timeout=30)

if disappeared:
    print("加载完成")
```

## OCR 文字识别

需要额外安装：
```bash
pip install paddlepaddle paddleocr
```

```python
# 识别屏幕中的文字
texts = cv.ocr_text()

for item in texts:
    print(f"文字: {item['text']}")
    print(f"置信度: {item['confidence']:.2%}")
    print(f"位置: {item['bounds']}")
```

**输出示例：**
```python
[
    {"text": "确定", "confidence": 0.95, "bounds": (100, 200, 150, 230)},
    {"text": "取消", "confidence": 0.93, "bounds": (200, 200, 250, 230)},
]
```

### 查找文字

```python
# 在屏幕中查找包含指定文字的元素
results = cv.find_text("确定", confidence=0.8)

for item in results:
    print(f"找到文字 '{item['text']}' at {item['bounds']}")
    # 点击该位置
    x, y = (item['bounds'][0] + item['bounds'][2]) // 2, \
           (item['bounds'][1] + item['bounds'][3]) // 2
    ui.click(x, y)
```

## 图像对比

### 比较相似度

```python
# 比较两张图像的相似度
similarity = cv.compare_images("before.png", "after.png")
print(f"相似度: {similarity:.2%}")
```

## 颜色检测

```python
# 检测屏幕中的指定颜色区域
colors = cv.detect_colors()

# 默认检测红、绿、蓝三种颜色
print(colors["red"])      # 红色像素坐标列表
print(colors["green"])   # 绿色像素坐标列表
print(colors["blue"])    # 蓝色像素坐标列表
```

### 自定义颜色范围

```python
color_range = {
    "yellow": ((20, 100, 100), (40, 255, 255)),  # HSV 范围
    "purple": ((130, 50, 50), (160, 255, 255)),
}

colors = cv.detect_colors(color_range=color_range)
```

## 获取像素颜色

```python
# 获取指定点的 BGR 颜色值
bgr = cv.get_pixel_color(100, 200)
print(f"BGR: {bgr}")  # 例如 (255, 0, 0) 表示红色
```

## 完整示例

```python
from hdctool import create_client

client = create_client()
target = client.get_target(client.list_targets()[0])
ui = target.create_ui_driver()
cv = ui.cv

try:
    # 等待目标界面出现
    result = cv.wait_for_image("target_ui.png", timeout=15)
    if result:
        # 点击进入
        cv.find_and_click("enter_button.png")
        
        # 等待加载完成
        cv.wait_for_image_disappear("loading.png", timeout=30)
        
        # 验证文字
        texts = cv.find_text("成功")
        assert len(texts) > 0, "未找到成功提示"
        
finally:
    ui.stop()
```
