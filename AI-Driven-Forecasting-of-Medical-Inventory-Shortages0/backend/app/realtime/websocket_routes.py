from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.realtime.connection_manager import socket_manager

router = APIRouter()


@router.websocket("/ws/{channel}")
async def websocket_endpoint(websocket: WebSocket, channel: str):
    await socket_manager.connect(channel, websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        socket_manager.disconnect(channel, websocket)
