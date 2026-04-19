import time
from pathlib import Path

import hdctool

CAPTURE_DIR = Path(__file__).resolve().parent / "capture_frames"


def _frame_suffix(data: bytes) -> str:
    if len(data) >= 3 and data[:3] == b"\xff\xd8\xff":
        return ".jpg"
    if len(data) >= 8 and data[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    if len(data) >= 6 and data[:6] in (b"GIF87a", b"GIF89a"):
        return ".gif"
    return ".bin"


def main() -> None:
    client = hdctool.create_client()
    targets = client.list_targets()
    if not targets:
        print("未检测到设备")
        return

    target = client.get_target(targets[0])
    params = target.get_parameters()
    print("设备名:", params.get("const.product.name"))

    ui = None
    try:
        ui = target.create_ui_driver()
        size = ui.get_display_size()
        print("UiDriver.get_display_size:", size)

        layout = ui.capture_layout()
        text = layout if isinstance(layout, str) else repr(layout)
        print("UiDriver.capture_layout (节选):", text[:400] + ("..." if len(text) > 400 else ""))

        w, h = (size.get("width"), size.get("height")) if isinstance(size, dict) else (720, 1280)
        x, y = w // 2, h // 3
        ui.touch_down(x, y)
        ui.touch_up(x, y)
        ui.input_text("hello", x=0, y=0)

        CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
        frame_idx = 0

        def on_frame(data: bytes) -> None:
            nonlocal frame_idx
            frame_idx += 1
            ext = _frame_suffix(data)
            path = CAPTURE_DIR / f"frame_{frame_idx:04d}{ext}"
            path.write_bytes(data)
            print(f"已保存: {path} ({len(data)} bytes)")

        ui.start_capture_screen(on_frame)
        time.sleep(1)
        ui.stop_capture_screen()
        print(f"共写入 {frame_idx} 帧 -> {CAPTURE_DIR}")

    except Exception as e:
        print("UiDriver 调用失败（检查设备、Hypium/uitest 与 agent .so）:", e)
    finally:
        if ui is not None:
            ui.stop()


if __name__ == "__main__":
    main()
