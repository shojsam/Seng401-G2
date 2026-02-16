from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/")
async def create_lobby():
    # TODO: create lobby in Redis, record in MySQL
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/")
async def list_lobbies():
    # TODO: return joinable lobbies
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/{lobby_id}")
async def get_lobby(lobby_id: str):
    # TODO: return lobby details
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/{lobby_id}/join")
async def join_lobby(lobby_id: str):
    # TODO: add player to lobby
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/{lobby_id}/leave")
async def leave_lobby(lobby_id: str):
    # TODO: remove player from lobby
    raise HTTPException(status_code=501, detail="Not implemented")
