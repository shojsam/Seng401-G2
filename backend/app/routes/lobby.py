from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.data.redis_client import redis_client

router = APIRouter()

LOBBY_KEY = "lobby:players"


class JoinRequest(BaseModel):
    username: str


@router.post("/join")
async def join_lobby(req: JoinRequest):
    username = req.username.strip()
    if not username:
        raise HTTPException(status_code=400, detail="Username cannot be empty")
    if redis_client.sismember(LOBBY_KEY, username):
        raise HTTPException(status_code=409, detail="Username already taken in lobby")
    redis_client.sadd(LOBBY_KEY, username)
    return {"message": f"{username} joined the lobby", "username": username}


@router.post("/leave")
async def leave_lobby(req: JoinRequest):
    username = req.username.strip()
    redis_client.srem(LOBBY_KEY, username)
    return {"message": f"{username} left the lobby"}


@router.get("/players")
async def get_players():
    players = redis_client.smembers(LOBBY_KEY)
    return {"players": list(players)}
