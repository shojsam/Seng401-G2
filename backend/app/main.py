from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .data.database import get_connection
from .data.seed import initialize_and_seed_database
from .routes import lobby, results
from .ws import game
from .data import repository


app = FastAPI(title="Greenwashed", version="0.1.0")

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
    try:
        conn = get_connection()
        conn.close()
        initialize_and_seed_database()
    except Exception as exc:
        print(f"Database initialization unavailable at startup: {exc}")


@app.get("/health")
async def health_check():
    return {"status": "ok"}




@app.get("/cards")
def read_cards():
    return repository.get_all_cards()
