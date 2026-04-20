"""
CV - 图像识别模块

基于 OpenCV 的图像识别功能，支持模板匹配、特征点匹配等。
"""
from __future__ import annotations

import os
import time
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

if TYPE_CHECKING:
    from .driver import UiDriver

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


class CVPoint:
    """图像坐标点"""

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def __repr__(self) -> str:
        return f"CVPoint(x={self.x}, y={self.y})"

    def to_tuple(self) -> Tuple[int, int]:
        return (self.x, self.y)


class CVMatch:
    """图像匹配结果"""

    def __init__(
        self,
        confidence: float,
        x: int,
        y: int,
        width: int,
        height: int,
        template: Optional["np.ndarray"] = None,
    ):
        self.confidence = confidence
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.template = template

    @property
    def center(self) -> CVPoint:
        """获取匹配区域的中心点"""
        return CVPoint(
            self.x + self.width // 2,
            self.y + self.height // 2,
        )

    @property
    def bounds(self) -> Tuple[int, int, int, int]:
        """获取边界矩形 (left, top, right, bottom)"""
        return (self.x, self.y, self.x + self.width, self.y + self.height)

    def __repr__(self) -> str:
        return f"CVMatch(confidence={self.confidence:.2%}, center={self.center})"


class CV:
    """
    图像识别模块

    提供基于 OpenCV 的图像匹配、特征点检测等功能。

    Example:
        ```python
        driver = target.ui_driver()
        cv = driver.CV

        # 在屏幕截图中查找模板
        result = cv.find_image("template.png", source=screenshot)
        if result:
            x, y = result.center
            driver.click(x, y)
        ```
    """

    # 默认置信度阈值
    DEFAULT_THRESHOLD = 0.8
    # 低置信度阈值（用于多匹配）
    LOW_THRESHOLD = 0.6

    def __init__(self, driver: UiDriver):
        """
        初始化 CV 模块

        Args:
            driver: UiDriver 实例
        """
        if not CV2_AVAILABLE:
            raise ImportError(
                "OpenCV is not available. Please install opencv-python: pip install opencv-python"
            )

        self._driver = driver

    @property
    def driver(self) -> UiDriver:
        """获取关联的 UiDriver"""
        return self._driver

    def _load_image(self, image: Union[str, "np.ndarray"]) -> "np.ndarray":
        """
        加载图像

        Args:
            image: 图像路径或 numpy 数组

        Returns:
            OpenCV 图像矩阵
        """
        if isinstance(image, str):
            if not os.path.exists(image):
                raise FileNotFoundError(f"Image file not found: {image}")
            return cv2.imread(image)
        elif isinstance(image, np.ndarray):
            return image
        else:
            raise TypeError(f"Invalid image type: {type(image)}")

    def _capture_screen_temp(self) -> "np.ndarray":
        """截取当前屏幕并返回临时路径"""
        import tempfile

        temp_path = tempfile.mktemp(suffix=".png")
        self._driver._shell(f"snapshot_display -f {temp_path}")
        img = cv2.imread(temp_path)
        try:
            os.unlink(temp_path)
        except Exception:
            pass
        if img is None:
            raise ValueError("Failed to capture screen")
        return img

    def find_image(
        self,
        template: Union[str, "np.ndarray"],
        source: Optional[Union[str, "np.ndarray"]] = None,
        threshold: float = DEFAULT_THRESHOLD,
        region: Optional[Tuple[int, int, int, int]] = None,
    ) -> Optional[CVMatch]:
        """
        在图像中查找模板（单匹配）

        Args:
            template: 模板图像路径或图像矩阵
            source: 源图像路径或图像矩阵（默认截取当前屏幕）
            threshold: 匹配阈值 (0-1)
            region: 搜索区域 (x, y, width, height)

        Returns:
            匹配结果，未找到返回 None
        """
        template_img = self._load_image(template)

        if source is None:
            source_img = self._capture_screen_temp()
        else:
            source_img = self._load_image(source)

        # 裁剪搜索区域
        if region:
            x, y, w, h = region
            source_img = source_img[y : y + h, x : x + w]

        # 模板匹配
        result = cv2.matchTemplate(source_img, template_img, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val >= threshold:
            h, w = template_img.shape[:2]
            return CVMatch(
                confidence=max_val,
                x=max_loc[0] + (region[0] if region else 0),
                y=max_loc[1] + (region[1] if region else 0),
                width=w,
                height=h,
                template=template_img,
            )

        return None

    def find_images(
        self,
        template: Union[str, "np.ndarray"],
        source: Optional[Union[str, "np.ndarray"]] = None,
        threshold: float = LOW_THRESHOLD,
        max_results: int = 10,
    ) -> List[CVMatch]:
        """
        在图像中查找所有匹配的模板

        Args:
            template: 模板图像路径或图像矩阵
            source: 源图像路径或图像矩阵（默认截取当前屏幕）
            threshold: 匹配阈值 (0-1)
            max_results: 最大返回结果数

        Returns:
            匹配结果列表
        """
        template_img = self._load_image(template)

        if source is None:
            source_img = self._capture_screen_temp()
        else:
            source_img = self._load_image(source)

        result = cv2.matchTemplate(source_img, template_img, cv2.TM_CCOEFF_NORMED)
        h, w = template_img.shape[:2]

        locations = np.where(result >= threshold)
        matches = []

        for pt in zip(*locations[::-1]):
            confidence = result[pt[1], pt[0]]
            matches.append(
                CVMatch(
                    confidence=confidence,
                    x=pt[0],
                    y=pt[1],
                    width=w,
                    height=h,
                    template=template_img,
                )
            )

        matches.sort(key=lambda m: m.confidence, reverse=True)

        # 去重
        filtered = []
        for match in matches[:max_results]:
            is_duplicate = False
            for existing in filtered:
                if (
                    abs(match.x - existing.x) < w // 2
                    and abs(match.y - existing.y) < h // 2
                ):
                    is_duplicate = True
                    break
            if not is_duplicate:
                filtered.append(match)

        return filtered

    def match_image(
        self,
        template: Union[str, "np.ndarray"],
        source: Optional[Union[str, "np.ndarray"]] = None,
    ) -> float:
        """
        计算模板与图像的最佳匹配度

        Args:
            template: 模板图像
            source: 源图像（默认截取当前屏幕）

        Returns:
            匹配度 (0-1)
        """
        template_img = self._load_image(template)

        if source is None:
            source_img = self._capture_screen_temp()
        else:
            source_img = self._load_image(source)

        result = cv2.matchTemplate(source_img, template_img, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(result)
        return float(max_val)

    def find_and_click(
        self,
        template: Union[str, "np.ndarray"],
        source: Optional[Union[str, "np.ndarray"]] = None,
        threshold: float = DEFAULT_THRESHOLD,
    ) -> bool:
        """
        查找图像并点击

        Args:
            template: 模板图像
            source: 源图像（默认截取当前屏幕）
            threshold: 匹配阈值

        Returns:
            是否成功找到并点击
        """
        match = self.find_image(template, source, threshold)
        if match:
            x, y = match.center.x, match.center.y
            self._driver.click(x, y)
            return True
        return False

    def wait_for_image(
        self,
        template: Union[str, "np.ndarray"],
        timeout: float = 10.0,
        interval: float = 0.5,
        threshold: float = DEFAULT_THRESHOLD,
    ) -> Optional[CVMatch]:
        """
        等待图像出现

        Args:
            template: 模板图像
            timeout: 超时时间（秒）
            interval: 轮询间隔（秒）
            threshold: 匹配阈值

        Returns:
            匹配结果，超时返回 None
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            match = self.find_image(template, None, threshold)
            if match:
                return match
            time.sleep(interval)
        return None

    def wait_for_image_disappear(
        self,
        template: Union[str, "np.ndarray"],
        timeout: float = 10.0,
        interval: float = 0.5,
        threshold: float = DEFAULT_THRESHOLD,
    ) -> bool:
        """
        等待图像消失

        Args:
            template: 模板图像
            timeout: 超时时间（秒）
            interval: 轮询间隔（秒）
            threshold: 匹配阈值

        Returns:
            是否在超时前消失
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            match = self.find_image(template, None, threshold)
            if not match:
                return True
            time.sleep(interval)
        return False

    def ocr_text(
        self,
        source: Optional[Union[str, "np.ndarray"]] = None,
        region: Optional[Tuple[int, int, int, int]] = None,
    ) -> List[Dict[str, Any]]:
        """
        OCR 文字识别

        注意：需要安装 paddlepaddle 和 paddleocr

        Args:
            source: 源图像（默认截取当前屏幕）
            region: 识别区域 (x, y, width, height)

        Returns:
            识别结果列表，每个元素包含 text, confidence, bounds
        """
        import tempfile

        try:
            from paddleocr import PaddleOCR
        except ImportError:
            raise ImportError(
                "PaddleOCR is not available. "
                "Please install: pip install paddlepaddle paddleocr"
            )

        if source is None:
            temp_path = tempfile.mktemp(suffix=".png")
            self._driver._shell(f"snapshot_display -f {temp_path}")
            source_img = temp_path
        else:
            source_img = source

        ocr = PaddleOCR(use_angle_cls=True, lang="ch")
        results = ocr.ocr(source_img)

        texts = []
        if results and results[0]:
            for line in results[0]:
                box = line[0]
                text = line[1][0]
                conf = line[1][1]

                x1 = min(p[0] for p in box)
                y1 = min(p[1] for p in box)
                x2 = max(p[0] for p in box)
                y2 = max(p[1] for p in box)

                texts.append(
                    {
                        "text": text,
                        "confidence": conf,
                        "bounds": (int(x1), int(y1), int(x2), int(y2)),
                    }
                )

        try:
            if source is None:
                os.unlink(temp_path)
        except Exception:
            pass

        return texts

    def find_text(
        self,
        text: str,
        source: Optional[Union[str, "np.ndarray"]] = None,
        confidence: float = 0.6,
    ) -> List[Dict[str, Any]]:
        """
        查找图像中的文字

        Args:
            text: 要查找的文字
            source: 源图像（默认截取当前屏幕）
            confidence: 识别置信度阈值

        Returns:
            匹配结果列表
        """
        results = self.ocr_text(source)
        matched = [
            r for r in results if text.lower() in r["text"].lower()
        ]
        return [r for r in matched if r["confidence"] >= confidence]

    def compare_images(
        self,
        image1: Union[str, "np.ndarray"],
        image2: Union[str, "np.ndarray"],
    ) -> float:
        """
        比较两张图像的相似度

        Args:
            image1: 第一张图像
            image2: 第二张图像

        Returns:
            相似度 (0-1)，1 表示完全相同
        """
        img1 = self._load_image(image1)
        img2 = self._load_image(image2)

        if img1.shape != img2.shape:
            img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))

        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

        hist1 = cv2.calcHist([gray1], [0], None, [256], [0, 256])
        hist2 = cv2.calcHist([gray2], [0], None, [256], [0, 256])

        hist1 = cv2.normalize(hist1, hist1).flatten()
        hist2 = cv2.normalize(hist2, hist2).flatten()

        similarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        return float(max(0, similarity))

    def detect_colors(
        self,
        source: Optional[Union[str, "np.ndarray"]] = None,
        color_range: Optional[Dict[str, Tuple[Tuple[int, int, int], Tuple[int, int, int]]]] = None,
    ) -> Dict[str, List[Tuple[int, int]]]:
        """
        检测图像中的指定颜色区域

        Args:
            source: 源图像（默认截取当前屏幕）
            color_range: 颜色范围字典

        Returns:
            每个颜色的像素点坐标列表
        """
        if source is None:
            source_img = self._capture_screen_temp()
        else:
            source_img = self._load_image(source)

        hsv = cv2.cvtColor(source_img, cv2.COLOR_BGR2HSV)

        result = {}

        if color_range is None:
            color_range = {
                "red": ((0, 100, 100), (10, 255, 255)),
                "green": ((35, 100, 100), (85, 255, 255)),
                "blue": ((100, 100, 100), (130, 255, 255)),
            }

        for name, (lower, upper) in color_range.items():
            lower_np = np.array(lower, dtype=np.uint8)
            upper_np = np.array(upper, dtype=np.uint8)

            mask = cv2.inRange(hsv, lower_np, upper_np)

            y_coords, x_coords = np.where(mask > 0)
            points = list(zip(x_coords.tolist(), y_coords.tolist()))

            result[name] = points

        return result

    def get_pixel_color(
        self,
        x: int,
        y: int,
        source: Optional[Union[str, "np.ndarray"]] = None,
    ) -> Tuple[int, int, int]:
        """
        获取指定像素点的颜色

        Args:
            x: X 坐标
            y: Y 坐标
            source: 源图像（默认截取当前屏幕）

        Returns:
            BGR 颜色值
        """
        if source is None:
            source_img = self._capture_screen_temp()
        else:
            source_img = self._load_image(source)

        return tuple(source_img[y, x].tolist())
