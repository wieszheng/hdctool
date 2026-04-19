from __future__ import annotations

from unittest.mock import MagicMock, patch

from hdctool.ui.driver import UiDriver


def test_ui_driver_subsystem_facades_are_cached() -> None:
    t = MagicMock()
    t.list_forwards.return_value = []
    d = UiDriver(t)
    assert d.target is t
    assert d.gestures is d.gestures
    assert d.app_manager is d.app_manager
    assert d.screen is d.screen
    assert d.storage is d.storage
    assert d.system is d.system
    assert d.hilog is d.hilog
    assert d.uinput is d.uinput


def test_storage_has_file_shell_quoted() -> None:
    t = MagicMock()
    t.list_forwards.return_value = []
    d = UiDriver(t)
    with patch.object(d, "_shell", return_value="OK") as sh:
        assert d.storage.has_file("/tmp/a b") is True
        cmd = sh.call_args[0][0]
    assert "test -e" in cmd
    assert "/tmp/a b" in cmd
