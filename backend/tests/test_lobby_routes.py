from fastapi.testclient import TestClient

from app.main import app


def test_create_lobby_rejects_blank_username(monkeypatch):
    client = TestClient(app)

    response = client.post("/lobby/create", json={"username": "   "})

    assert response.status_code == 400
    assert response.json()["detail"] == "Username cannot be empty"


def test_create_lobby_persists_creator(monkeypatch):
    client = TestClient(app)

    class Lobby:
        def __init__(self, code: str, players: set[str]):
            self.code = code
            self.players = players

    monkeypatch.setattr("app.routes.lobby.create_lobby", lambda: Lobby("ABC123", set()))
    monkeypatch.setattr(
        "app.routes.lobby.add_player",
        lambda lobby_code, username: Lobby(lobby_code, {username}),
    )

    response = client.post("/lobby/create", json={"username": " Sam "})

    assert response.status_code == 200
    assert response.json() == {
        "message": "Sam created lobby ABC123",
        "username": "Sam",
        "lobby_code": "ABC123",
    }


def test_join_lobby_rejects_duplicate_username(monkeypatch):
    client = TestClient(app)

    class Lobby:
        def __init__(self, code: str, players: set[str]):
            self.code = code
            self.players = players

    monkeypatch.setattr("app.routes.lobby.get_lobby", lambda code: Lobby("ABC123", {"Sam"}))

    response = client.post("/lobby/join", json={"username": "Sam", "lobby_code": "abc123"})

    assert response.status_code == 409
    assert response.json()["detail"] == "Username already taken in lobby"
