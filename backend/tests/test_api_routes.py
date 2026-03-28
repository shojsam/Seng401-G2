from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# Health route

def test_health_check_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# Lobby routes

@patch("app.routes.lobby.create_lobby")
@patch("app.routes.lobby.add_player")
def test_create_lobby_returns_code(mock_add, mock_create):
    from app.state.lobbies import LobbyState

    lobby = LobbyState(code="ABC123", players=set())
    mock_create.return_value = lobby
    mock_add.return_value = LobbyState(code="ABC123", players={"alice"})

    response = client.post("/lobby/create", json={"username": "alice"})
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "alice"
    assert data["lobby_code"] == "ABC123"


def test_create_lobby_rejects_blank_username():
    response = client.post("/lobby/create", json={"username": "   "})
    assert response.status_code == 400
    assert response.json()["detail"] == "Username cannot be empty"


@patch("app.routes.lobby.get_lobby")
def test_join_lobby_rejects_missing_lobby(mock_get):
    mock_get.return_value = None
    response = client.post("/lobby/join", json={"username": "alice", "lobby_code": "FAKE"})
    assert response.status_code == 404


def test_join_lobby_rejects_blank_username():
    response = client.post("/lobby/join", json={"username": "   ", "lobby_code": "ABC123"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Username cannot be empty"


# Results route

@patch("app.routes.results.get_recent_results")
def test_get_results_returns_list(mock_results):
    mock_results.return_value = [
        {"id": 1, "winner": "reformers", "played_at": "2026-03-16 10:00:00"},
        {"id": 2, "winner": "exploiters", "played_at": "2026-03-15 18:45:00"},
    ]
    response = client.get("/results/")
    assert response.status_code == 200
    payload = response.json()
    assert "results" in payload
    assert payload["results"][0]["winner"] == "reformers"
    assert payload["results"][1]["winner"] == "exploiters"
