from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.data.database import init_db
from app.routes import lobby, results
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
app.include_router(results.router, prefix="/results", tags=["results"])

# WebSocket
app.include_router(game.router, tags=["game"])


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
async def health_check():
    return {"status": "ok"}
