from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import asyncio
import time

router = APIRouter()

@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    # Logic will be injected from server or passed via state
    pass

@router.get("/health")
async def health():
    return {"status": "ok"}
