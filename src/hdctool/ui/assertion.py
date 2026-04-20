"""
Assert - 断言模块

提供类似 hypium 的断言功能，支持断言失败后自动截屏。
"""

from __future__ import annotations

import re
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .driver import UiDriver


class Assert:
    """
    基础断言操作类

    支持断言失败后自动截屏，提供多种断言方法。

    Example:
        ```python
        driver = target.ui_driver()
        driver.assertion.equal(1, 1)
        driver.assertion.contains("hello", "ell")
        driver.assertion.is_true(True)
        ```
    """

    def __init__(self, driver: UiDriver):
        """
        初始化断言模块

        Args:
            driver: UiDriver 实例
        """
        self._driver = driver
        self._screenshot_on_fail: bool = True
        self._last_screenshot_path: str | None = None

    @property
    def driver(self) -> UiDriver:
        """获取关联的 UiDriver"""
        return self._driver

    def enable_screenshot_on_fail(self, enabled: bool = True) -> None:
        """
        设置断言失败时自动截屏

        Args:
            enabled: 是否启用
        """
        self._screenshot_on_fail = enabled

    def _on_fail(
        self,
        fail_msg: str | None,
        actual: Any,
        expect: Any,
        condition_desc: str,
    ) -> None:
        """
        断言失败时的处理

        Args:
            fail_msg: 失败消息
            actual: 实际值
            expect: 期望值
            condition_desc: 条件描述
        """
        if self._screenshot_on_fail:
            try:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                screenshot_path = f"/tmp/assert_fail_{timestamp}.png"
                self._driver._shell(f"snapshot_display -f {screenshot_path}")
                self._last_screenshot_path = screenshot_path
            except Exception:
                pass

    def is_true(
        self,
        actual: bool,
        fail_msg: str | None = None,
    ) -> bool:
        """
        断言实际值为 True

        Args:
            actual: 实际值
            fail_msg: 失败时显示的消息

        Returns:
            断言结果

        Raises:
            AssertionError: 断言失败时抛出
        """
        if actual is not True:
            msg = fail_msg or f"期望值为 True，实际值为 {actual}"
            self._on_fail(msg, actual, True, "is True")
            raise AssertionError(msg)
        return True

    def is_false(
        self,
        actual: bool,
        fail_msg: str | None = None,
    ) -> bool:
        """
        断言实际值为 False

        Args:
            actual: 实际值
            fail_msg: 失败时显示的消息

        Returns:
            断言结果

        Raises:
            AssertionError: 断言失败时抛出
        """
        if actual is not False:
            msg = fail_msg or f"期望值为 False，实际值为 {actual}"
            self._on_fail(msg, actual, False, "is False")
            raise AssertionError(msg)
        return True

    def equal(
        self,
        actual: Any,
        expect: Any,
        fail_msg: str | None = None,
    ) -> bool:
        """
        断言实际值等于期望值

        Args:
            actual: 实际值
            expect: 期望值
            fail_msg: 失败时显示的消息

        Returns:
            断言结果

        Raises:
            AssertionError: 断言失败时抛出
        """
        if actual != expect:
            msg = fail_msg or f"期望值 {expect!r}，实际值 {actual!r}"
            self._on_fail(msg, actual, expect, "==")
            raise AssertionError(msg)
        return True

    def not_equal(
        self,
        actual: Any,
        expect: Any,
        fail_msg: str | None = None,
    ) -> bool:
        """
        断言实际值不等于期望值

        Args:
            actual: 实际值
            expect: 期望值
            fail_msg: 失败时显示的消息

        Returns:
            断言结果

        Raises:
            AssertionError: 断言失败时抛出
        """
        if actual == expect:
            msg = fail_msg or f"期望值不等于 {expect!r}，实际值相等"
            self._on_fail(msg, actual, expect, "!=")
            raise AssertionError(msg)
        return True

    def contains(
        self,
        actual: str,
        expect: str,
        fail_msg: str | None = None,
    ) -> bool:
        """
        断言实际字符串包含期望子串

        Args:
            actual: 实际字符串
            expect: 期望包含的子串
            fail_msg: 失败时显示的消息

        Returns:
            断言结果

        Raises:
            AssertionError: 断言失败时抛出
        """
        if expect not in actual:
            msg = fail_msg or f"期望 '{actual}' 包含 '{expect}'"
            self._on_fail(msg, actual, expect, "contains")
            raise AssertionError(msg)
        return True

    def not_contains(
        self,
        actual: str,
        expect: str,
        fail_msg: str | None = None,
    ) -> bool:
        """
        断言实际字符串不包含期望子串

        Args:
            actual: 实际字符串
            expect: 期望不包含的子串
            fail_msg: 失败时显示的消息

        Returns:
            断言结果

        Raises:
            AssertionError: 断言失败时抛出
        """
        if expect in actual:
            msg = fail_msg or f"期望 '{actual}' 不包含 '{expect}'"
            self._on_fail(msg, actual, expect, "not contains")
            raise AssertionError(msg)
        return True

    def starts_with(
        self,
        actual: str,
        expect: str,
        fail_msg: str | None = None,
    ) -> bool:
        """
        断言实际字符串以期望前缀开头

        Args:
            actual: 实际字符串
            expect: 期望前缀
            fail_msg: 失败时显示的消息

        Returns:
            断言结果

        Raises:
            AssertionError: 断言失败时抛出
        """
        if not actual.startswith(expect):
            msg = fail_msg or f"期望 '{actual}' 以 '{expect}' 开头"
            self._on_fail(msg, actual, expect, "starts_with")
            raise AssertionError(msg)
        return True

    def ends_with(
        self,
        actual: str,
        expect: str,
        fail_msg: str | None = None,
    ) -> bool:
        """
        断言实际字符串以期望后缀结尾

        Args:
            actual: 实际字符串
            expect: 期望后缀
            fail_msg: 失败时显示的消息

        Returns:
            断言结果

        Raises:
            AssertionError: 断言失败时抛出
        """
        if not actual.endswith(expect):
            msg = fail_msg or f"期望 '{actual}' 以 '{expect}' 结尾"
            self._on_fail(msg, actual, expect, "ends_with")
            raise AssertionError(msg)
        return True

    def match_regexp(
        self,
        actual: str,
        pattern: str,
        fail_msg: str | None = None,
    ) -> bool:
        """
        断言实际字符串匹配正则表达式

        Args:
            actual: 实际字符串
            pattern: 正则表达式模式
            fail_msg: 失败时显示的消息

        Returns:
            断言结果

        Raises:
            AssertionError: 断言失败时抛出
        """
        result = re.search(pattern, actual)
        if result is None:
            msg = fail_msg or f"期望 '{actual}' 匹配正则 '{pattern}'"
            self._on_fail(msg, actual, pattern, "match_regexp")
            raise AssertionError(msg)
        return True

    def greater(
        self,
        actual: float,
        expect: float,
        fail_msg: str | None = None,
    ) -> bool:
        """
        断言实际值大于期望值

        Args:
            actual: 实际值
            expect: 期望值
            fail_msg: 失败时显示的消息

        Returns:
            断言结果

        Raises:
            AssertionError: 断言失败时抛出
        """
        if actual <= expect:
            msg = fail_msg or f"期望 {actual} > {expect}"
            self._on_fail(msg, actual, expect, ">")
            raise AssertionError(msg)
        return True

    def greater_equal(
        self,
        actual: float,
        expect: float,
        fail_msg: str | None = None,
    ) -> bool:
        """
        断言实际值大于等于期望值

        Args:
            actual: 实际值
            expect: 期望值
            fail_msg: 失败时显示的消息

        Returns:
            断言结果

        Raises:
            AssertionError: 断言失败时抛出
        """
        if actual < expect:
            msg = fail_msg or f"期望 {actual} >= {expect}"
            self._on_fail(msg, actual, expect, ">=")
            raise AssertionError(msg)
        return True

    def less(
        self,
        actual: float,
        expect: float,
        fail_msg: str | None = None,
    ) -> bool:
        """
        断言实际值小于期望值

        Args:
            actual: 实际值
            expect: 期望值
            fail_msg: 失败时显示的消息

        Returns:
            断言结果

        Raises:
            AssertionError: 断言失败时抛出
        """
        if actual >= expect:
            msg = fail_msg or f"期望 {actual} < {expect}"
            self._on_fail(msg, actual, expect, "<")
            raise AssertionError(msg)
        return True

    def less_equal(
        self,
        actual: float,
        expect: float,
        fail_msg: str | None = None,
    ) -> bool:
        """
        断言实际值小于等于期望值

        Args:
            actual: 实际值
            expect: 期望值
            fail_msg: 失败时显示的消息

        Returns:
            断言结果

        Raises:
            AssertionError: 断言失败时抛出
        """
        if actual > expect:
            msg = fail_msg or f"期望 {actual} <= {expect}"
            self._on_fail(msg, actual, expect, "<=")
            raise AssertionError(msg)
        return True

    def is_none(
        self,
        actual: Any,
        fail_msg: str | None = None,
    ) -> bool:
        """
        断言实际值为 None

        Args:
            actual: 实际值
            fail_msg: 失败时显示的消息

        Returns:
            断言结果

        Raises:
            AssertionError: 断言失败时抛出
        """
        if actual is not None:
            msg = fail_msg or f"期望值为 None，实际值为 {actual!r}"
            self._on_fail(msg, actual, None, "is None")
            raise AssertionError(msg)
        return True

    def is_not_none(
        self,
        actual: Any,
        fail_msg: str | None = None,
    ) -> bool:
        """
        断言实际值不为 None

        Args:
            actual: 实际值
            fail_msg: 失败时显示的消息

        Returns:
            断言结果

        Raises:
            AssertionError: 断言失败时抛出
        """
        if actual is None:
            msg = fail_msg or "期望值不为 None"
            self._on_fail(msg, actual, "not None", "is not None")
            raise AssertionError(msg)
        return True

    def in_range(
        self,
        actual: float,
        min_val: float,
        max_val: float,
        fail_msg: str | None = None,
    ) -> bool:
        """
        断言实际值在指定范围内

        Args:
            actual: 实际值
            min_val: 最小值
            max_val: 最大值
            fail_msg: 失败时显示的消息

        Returns:
            断言结果

        Raises:
            AssertionError: 断言失败时抛出
        """
        if not (min_val <= actual <= max_val):
            msg = fail_msg or f"期望值 {actual} 在范围 [{min_val}, {max_val}] 内"
            self._on_fail(msg, actual, f"[{min_val}, {max_val}]", "in_range")
            raise AssertionError(msg)
        return True

    def length_equal(
        self,
        actual: str,
        expect_length: int,
        fail_msg: str | None = None,
    ) -> bool:
        """
        断言字符串长度等于期望值

        Args:
            actual: 实际字符串
            expect_length: 期望长度
            fail_msg: 失败时显示的消息

        Returns:
            断言结果

        Raises:
            AssertionError: 断言失败时抛出
        """
        actual_length = len(actual)
        if actual_length != expect_length:
            msg = fail_msg or f"期望长度 {expect_length}，实际长度 {actual_length}"
            self._on_fail(msg, actual_length, expect_length, "len ==")
            raise AssertionError(msg)
        return True

    @property
    def last_screenshot_path(self) -> str | None:
        """
        获取最后一次断言失败时的截图路径

        Returns:
            截图路径，如果未失败截屏则为 None
        """
        return self._last_screenshot_path
