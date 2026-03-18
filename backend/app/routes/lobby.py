from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..state.lobbies import create_lobby, get_lobby, normalize_lobby_code, remove_player

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
    lobby.players.add(username)
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

    lobby.players.add(username)
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
    lobby = get_lobby(lobby_code)
    if lobby is None:
        raise HTTPException(status_code=404, detail="Lobby not found")
    return {"lobby_code": lobby.code, "players": list(lobby.players)}
