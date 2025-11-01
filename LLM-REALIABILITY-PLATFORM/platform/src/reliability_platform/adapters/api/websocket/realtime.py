 from __future__ import annotations

 from fastapi import APIRouter, WebSocket


 router = APIRouter()


 @router.websocket("/ws/realtime")
 async def realtime(ws: WebSocket) -> None:
     await ws.accept()
     await ws.send_json({"message": "connected"})
     await ws.close()


