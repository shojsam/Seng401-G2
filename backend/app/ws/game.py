from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

# Track active connections: lobby_id -> {player_id: websocket}
active_connections: dict[str, dict[str, WebSocket]] = {}


@router.websocket("/ws/{lobby_id}/{player_id}")
async def game_ws(websocket: WebSocket, lobby_id: str, player_id: str):
    await websocket.accept()

    if lobby_id not in active_connections:
        active_connections[lobby_id] = {}
    active_connections[lobby_id][player_id] = websocket

    try:
        while True:
            data = await websocket.receive_json()
            # TODO: route message to game engine based on data["type"]
            # e.g. "start_game", "propose_policy", "vote", "chat"
    except WebSocketDisconnect:
        active_connections[lobby_id].pop(player_id, None)
        if not active_connections[lobby_id]:
            del active_connections[lobby_id]


async def broadcast(lobby_id: str, message: dict):
    """Send a message to all players in a lobby."""
    connections = active_connections.get(lobby_id, {})
    for ws in connections.values():
        await ws.send_json(message)


async def send_to_player(lobby_id: str, player_id: str, message: dict):
    """Send a private message to a specific player."""
    ws = active_connections.get(lobby_id, {}).get(player_id)
    if ws:
        await ws.send_json(message)
