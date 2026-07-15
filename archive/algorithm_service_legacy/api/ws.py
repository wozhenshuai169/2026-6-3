"""WebSocket 端点 — 流式推送讲解 / 回答文本（Mock）。"""

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


@router.websocket("/ws/explanation/{roomId}")
async def ws_explanation(ws: WebSocket, roomId: str):
    await ws.accept()
    try:
        chunks = [
            f"【{roomId}】欢迎来到景区…",
            "这里是语音讲解内容第一段…",
            "接下来是第二段讲解…",
            "讲解完毕，请继续前行。",
            '{"type":"done","message":"stream finished"}',
        ]
        for chunk in chunks:
            await ws.send_text(chunk)
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass


@router.websocket("/ws/answer/{roomId}/{userId}")
async def ws_answer(ws: WebSocket, roomId: str, userId: str):
    await ws.accept()
    try:
        chunks = [
            f"【{roomId}/{userId}】正在查询…",
            "根据景区知识库，这个建筑…",
            "答案是：建于清代乾隆年间。",
            '{"type":"done","message":"stream finished"}',
        ]
        for chunk in chunks:
            await ws.send_text(chunk)
            await asyncio.sleep(0.8)
    except WebSocketDisconnect:
        pass
