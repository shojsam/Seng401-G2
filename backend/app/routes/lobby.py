from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..state.lobbies import (
    LobbyPlayerExistsError,
    add_player,
    create_lobby,
    get_lobby,
    get_lobby_players,
    normalize_lobby_code,
    remove_player,
)

router = APIRouter()


class CreateLobbyRequest(BaseModel):
    username: str


class JoinRequest(BaseModel):
    username: str
    lobby_code: str


@router.post("/create")
async def create_lobby_route(req: CreateLobbyRequest):
    username = req.username.strip()
    if not username:
        raise HTTPException(status_code=400, detail="Username cannot be empty")

    lobby = create_lobby()
    try:
        lobby = add_player(lobby.code, username)
    except LobbyPlayerExistsError:
        raise HTTPException(status_code=409, detail="Username already taken in lobby") from None
    if lobby is None:
        raise HTTPException(status_code=500, detail="Failed to create lobby")
    return {
        "message": f"{username} created lobby {lobby.code}",
        "username": username,
        "lobby_code": lobby.code,
    }


@router.post("/join")
async def join_lobby(req: JoinRequest):
    username = req.username.strip()
    lobby_code = normalize_lobby_code(req.lobby_code)

    if not username:
        raise HTTPException(status_code=400, detail="Username cannot be empty")
    if not lobby_code:
        raise HTTPException(status_code=400, detail="Lobby code cannot be empty")

    lobby = get_lobby(lobby_code)
    if lobby is None:
        raise HTTPException(status_code=404, detail="Lobby not found")
    if username in lobby.players:
        raise HTTPException(status_code=409, detail="Username already taken in lobby")

    try:
        lobby = add_player(lobby.code, username)
    except LobbyPlayerExistsError:
        raise HTTPException(status_code=409, detail="Username already taken in lobby") from None
    if lobby is None:
        raise HTTPException(status_code=404, detail="Lobby not found")
    return {
        "message": f"{username} joined lobby {lobby.code}",
        "username": username,
        "lobby_code": lobby.code,
    }


@router.post("/leave")
async def leave_lobby(req: JoinRequest):
    username = req.username.strip()
    lobby_code = normalize_lobby_code(req.lobby_code)
    lobby = get_lobby(lobby_code)
    if lobby is None:
        return {"message": f"Lobby {lobby_code} does not exist"}

    remove_player(lobby, username)
    return {"message": f"{username} left lobby {lobby_code}"}


@router.get("/{lobby_code}/players")
async def get_players(lobby_code: str):
    players = get_lobby_players(lobby_code)
    normalized_code = normalize_lobby_code(lobby_code)
    if players is None:
        raise HTTPException(status_code=404, detail="Lobby not found")
    return {"lobby_code": normalized_code, "players": players}
