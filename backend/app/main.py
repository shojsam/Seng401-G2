from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import auth, lobby, match
from app.ws import game

app = FastAPI(title="GreenWatch", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REST routes
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(lobby.router, prefix="/lobbies", tags=["lobbies"])
app.include_router(match.router, prefix="/matches", tags=["matches"])

# WebSocket
app.include_router(game.router, tags=["game"])


@app.get("/health")
async def health_check():
    return {"status": "ok"}
