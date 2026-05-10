from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import asyncio

router = APIRouter()

# The actual logic is injected/managed in server.py, this acts as the interface definition
@router.websocket("/ws/brain")
async def ws_brain(websocket: WebSocket):
    await websocket.accept()
    # Logic in server.py
    pass
