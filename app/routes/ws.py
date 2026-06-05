import asyncio
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

logger = logging.getLogger(__name__)

# In-memory connection registry: session_id → list of WebSocket connections
_connections: dict[str, list[WebSocket]] = {}
_lock = asyncio.Lock()


@router.websocket("/sessions/{session_id}/ws")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()

    async with _lock:
        if session_id not in _connections:
            _connections[session_id] = []
        _connections[session_id].append(websocket)

    try:
        # Keep the connection alive, receive client messages (e.g., pings)
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        pass
    finally:
        async with _lock:
            _connections[session_id].remove(websocket)
            if not _connections[session_id]:
                del _connections[session_id]


async def send_execution_log(session_id: str, message: str):
    """Push a log message to all WebSocket clients for a session."""
    async with _lock:
        conns = list(_connections.get(session_id, []))
    for ws in conns:
        try:
            await ws.send_json({"type": "log", "content": message})
        except WebSocketDisconnect:
            pass
        except Exception:
            logger.debug("Failed to send log to websocket", exc_info=True)


async def send_agent_progress(session_id: str, status: str, data: dict | None = None):
    """Send agent progress update to WebSocket clients."""
    async with _lock:
        conns = list(_connections.get(session_id, []))
    payload = {"type": "progress", "status": status, "data": data or {}}
    for ws in conns:
        try:
            await ws.send_json(payload)
        except WebSocketDisconnect:
            pass
        except Exception:
            logger.debug("Failed to send progress to websocket", exc_info=True)
