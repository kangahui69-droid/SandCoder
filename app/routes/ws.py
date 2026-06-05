from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

# In-memory connection registry: session_id → list of WebSocket connections
_connections: dict[str, list[WebSocket]] = {}


@router.websocket("/sessions/{session_id}/ws")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()

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
        _connections[session_id].remove(websocket)
        if not _connections[session_id]:
            del _connections[session_id]


async def send_execution_log(session_id: str, message: str):
    """Push a log message to all WebSocket clients for a session."""
    if session_id in _connections:
        for ws in _connections[session_id]:
            try:
                await ws.send_json({"type": "log", "content": message})
            except Exception:
                pass


async def send_agent_progress(session_id: str, status: str, data: dict | None = None):
    """Send agent progress update to WebSocket clients."""
    if session_id in _connections:
        payload = {"type": "progress", "status": status, "data": data or {}}
        for ws in _connections[session_id]:
            try:
                await ws.send_json(payload)
            except Exception:
                pass
