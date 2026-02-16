from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

# Track active connections: username -> websocket
active_connections: dict[str, WebSocket] = {}


@router.websocket("/ws/{username}")
async def game_ws(websocket: WebSocket, username: str):
    await websocket.accept()
    active_connections[username] = websocket

    try:
        while True:
            data = await websocket.receive_json()
            # TODO: route message to game engine based on data["type"]
            # e.g. "start_game", "propose_policy", "vote", "chat"
    except WebSocketDisconnect:
        active_connections.pop(username, None)


async def broadcast(message: dict):
    """Send a message to all connected players."""
    for ws in active_connections.values():
        await ws.send_json(message)


async def send_to_player(username: str, message: dict):
    """Send a private message to a specific player."""
    ws = active_connections.get(username)
    if ws:
        await ws.send_json(message)
