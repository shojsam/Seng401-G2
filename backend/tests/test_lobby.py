import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes.lobby import router, lobby_players 

app = FastAPI()
app.include_router(router)

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_lobby():
    lobby_players.clear()
    yield
    lobby_players.clear()


def test_join_success():
    response = client.post("/join", json={"username": "Alice"})
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "Alice"
    assert "joined the lobby" in data["message"]


def test_join_empty_username():
    response = client.post("/join", json={"username": "   "})
    assert response.status_code == 400
    assert response.json()["detail"] == "Username cannot be empty"


def test_join_duplicate_username():
    client.post("/join", json={"username": "Alice"})
    response = client.post("/join", json={"username": "Alice"})
    assert response.status_code == 409
    assert response.json()["detail"] == "Username already taken in lobby"


def test_leave_lobby():
    client.post("/join", json={"username": "Alice"})
    response = client.post("/leave", json={"username": "Alice"})
    assert response.status_code == 200
    assert "left the lobby" in response.json()["message"]

    players = client.get("/players").json()["players"]
    assert "Alice" not in players


def test_leave_nonexistent_user():
    response = client.post("/leave", json={"username": "Ghost"})
    assert response.status_code == 200
    assert "left the lobby" in response.json()["message"]


def test_get_players_empty():
    response = client.get("/players")
    assert response.status_code == 200
    assert response.json()["players"] == []


def test_get_players_after_joins():
    client.post("/join", json={"username": "Alice"})
    client.post("/join", json={"username": "Bob"})

    response = client.get("/players")
    assert response.status_code == 200
    players = response.json()["players"]

    assert set(players) == {"Alice", "Bob"}