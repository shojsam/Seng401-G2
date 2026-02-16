from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

lobby_players: set[str] = set()


class JoinRequest(BaseModel):
    username: str


@router.post("/join")
async def join_lobby(req: JoinRequest):
    username = req.username.strip()
    if not username:
        raise HTTPException(status_code=400, detail="Username cannot be empty")
    if username in lobby_players:
        raise HTTPException(status_code=409, detail="Username already taken in lobby")
    lobby_players.add(username)
    return {"message": f"{username} joined the lobby", "username": username}


@router.post("/leave")
async def leave_lobby(req: JoinRequest):
    username = req.username.strip()
    lobby_players.discard(username)
    return {"message": f"{username} left the lobby"}


@router.get("/players")
async def get_players():
    return {"players": list(lobby_players)}
