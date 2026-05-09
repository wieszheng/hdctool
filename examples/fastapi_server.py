"""
FastAPI + Tracker 集成示例

安装依赖:
    pip install fastapi uvicorn

运行:
    uvicorn examples.fastapi_server:app --reload
    # 或从项目根目录
    python -m uvicorn examples.fastapi_server:app --reload

接口:
    GET  /targets          - 查询当前已连接设备列表
    WS   /ws/targets       - WebSocket 实时推送设备增减事件
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from hdctool import Client

client = Client()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # 应用关闭时无需额外清理，各 WebSocket 连接断开时已各自 end()


app = FastAPI(title="HDC Device API", lifespan=lifespan)


# ---------------------------------------------------------------------------
# REST
# ---------------------------------------------------------------------------


@app.get("/targets")
def list_targets() -> dict:
    """返回当前已连接设备列表（一次性查询）。"""
    return {"targets": client.list_targets()}


# ---------------------------------------------------------------------------
# WebSocket —— 实时设备变化推送
# ---------------------------------------------------------------------------


@app.websocket("/ws/targets")
async def ws_targets(websocket: WebSocket) -> None:
    """
    实时推送设备上线 / 下线事件。

    消息格式：
        {"event": "add",    "target": "<connect_key>"}
        {"event": "remove", "target": "<connect_key>"}
        {"event": "error",  "message": "<err>"}
    """
    await websocket.accept()

    # asyncio.Queue 桥接 Tracker 线程回调 → asyncio 协程
    queue: asyncio.Queue[dict] = asyncio.Queue()
    loop = asyncio.get_event_loop()

    def on_add(target: str) -> None:
        loop.call_soon_threadsafe(queue.put_nowait, {"event": "add", "target": target})

    def on_remove(target: str) -> None:
        loop.call_soon_threadsafe(queue.put_nowait, {"event": "remove", "target": target})

    def on_error(exc: Exception) -> None:
        loop.call_soon_threadsafe(
            queue.put_nowait, {"event": "error", "message": str(exc)}
        )

    tracker = client.track_targets()
    tracker.on("add", on_add)
    tracker.on("remove", on_remove)
    tracker.on("error", on_error)

    try:
        while True:
            msg = await queue.get()
            await websocket.send_json(msg)
    except WebSocketDisconnect:
        pass
    finally:
        tracker.end()
