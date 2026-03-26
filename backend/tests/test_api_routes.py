from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.main import app
from app.routes.lobby import lobby_players
from app.data.database import get_db


class FakeQuery:
    def order_by(self, *args, **kwargs):
        return self

    def all(self):
        return [
            SimpleNamespace(id=1, winner='reformers', played_at='2026-03-16 10:00:00'),
            SimpleNamespace(id=2, winner='draw', played_at='2026-03-15 18:45:00'),
        ]


class FakeSession:
    def query(self, model):
        return FakeQuery()


def override_get_db():
    yield FakeSession()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def setup_function():
    lobby_players.clear()


def teardown_function():
    lobby_players.clear()


# Health route

def test_health_check_returns_ok():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}


# Lobby routes

def test_join_lobby_accepts_valid_username():
    response = client.post('/lobby/join', json={'username': 'alice'})
    assert response.status_code == 200
    assert response.json()['username'] == 'alice'
    assert 'alice' in lobby_players


def test_join_lobby_rejects_blank_username():
    response = client.post('/lobby/join', json={'username': '   '})
    assert response.status_code == 400
    assert response.json()['detail'] == 'Username cannot be empty'


def test_join_lobby_rejects_duplicate_username():
    client.post('/lobby/join', json={'username': 'alice'})
    response = client.post('/lobby/join', json={'username': 'alice'})
    assert response.status_code == 409
    assert response.json()['detail'] == 'Username already taken in lobby'


def test_leave_lobby_removes_player_when_present():
    client.post('/lobby/join', json={'username': 'alice'})
    response = client.post('/lobby/leave', json={'username': 'alice'})
    assert response.status_code == 200
    assert 'alice' not in lobby_players


def test_leave_lobby_is_idempotent_for_unknown_player():
    response = client.post('/lobby/leave', json={'username': 'ghost'})
    assert response.status_code == 200
    assert response.json()['message'] == 'ghost left the lobby'


def test_get_players_returns_all_joined_players():
    client.post('/lobby/join', json={'username': 'alice'})
    client.post('/lobby/join', json={'username': 'bob'})
    response = client.get('/lobby/players')
    assert response.status_code == 200
    assert set(response.json()['players']) == {'alice', 'bob'}


# Results route

def test_get_results_returns_serialized_game_results():
    response = client.get('/results/')
    assert response.status_code == 200
    payload = response.json()
    assert 'results' in payload
    assert payload['results'][0]['winner'] == 'reformers'
    assert payload['results'][1]['winner'] == 'draw'
