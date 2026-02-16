from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import lobby
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
app.include_router(lobby.router, prefix="/lobby", tags=["lobby"])

# WebSocket
app.include_router(game.router, tags=["game"])


@app.get("/health")
async def health_check():
    return {"status": "ok"}
