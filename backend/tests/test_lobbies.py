import pytest
from unittest.mock import patch, MagicMock
from mysql.connector import IntegrityError 

from app.state.lobbies import (
    LobbyState,
    lobbies,
    normalize_lobby_code,
    get_lobby,
    get_or_create_lobby,
    create_lobby,
    add_player,
    get_lobby_players,
    remove_player,
    reset_lobby,
    LobbyPlayerExistsError,
)

@pytest.fixture(autouse=True)
def mock_db_connection():
    with patch("app.state.lobbies.get_connection") as mock_conn:
        mock_cursor = MagicMock()
        mock_conn.return_value.cursor.return_value = mock_cursor
        yield mock_conn, mock_cursor

def test_normalize_lobby_code():
    assert normalize_lobby_code(" abc123 ") == "ABC123"
    assert normalize_lobby_code("XYZ") == "XYZ"

def test_get_or_create_lobby_creates_new(mock_db_connection):
    mock_conn, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = None

    lobby = get_or_create_lobby("NEWCODE")
    assert isinstance(lobby, LobbyState)
    assert lobby.code == "NEWCODE"
    assert lobby.code in lobbies

def test_create_lobby(mock_db_connection):
    mock_conn, mock_cursor = mock_db_connection
    mock_cursor.execute.side_effect = [None] 

    lobby = create_lobby()
    assert isinstance(lobby, LobbyState)
    assert len(lobby.code) == 6
    assert lobby.code in lobbies

def test_add_player_success(mock_db_connection):
    mock_conn, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = (1,) 

    lobby_code = "LOBBY1"
    username = "Alice"
    lobby = add_player(lobby_code, username)
    assert isinstance(lobby, LobbyState)
    assert username not in lobby.ready_players

def test_add_player_existing_player_raises(mock_db_connection):
    mock_conn, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = (1,) 
    mock_cursor.execute.side_effect = [None, IntegrityError()] 

    with pytest.raises(LobbyPlayerExistsError):
        add_player("LOBBY1", "Alice")

def test_get_lobby_players_returns_sorted(mock_db_connection):
    mock_conn, mock_cursor = mock_db_connection
    mock_cursor.fetchall.return_value = [("Bob",), ("Alice",)]
    players = get_lobby_players("LOBBY1")
    assert players == ["Alice", "Bob"]

def test_remove_player_updates_lobby(mock_db_connection):
    mock_conn, mock_cursor = mock_db_connection
    lobby = LobbyState(code="LOBBY1", players={"Alice", "Bob"}, ready_players={"Alice"})
    lobbies[lobby.code] = lobby

    remove_player(lobby, "Alice")
    assert "Alice" not in lobby.ready_players
    assert "Alice" not in lobby.players

def test_reset_lobby_clears_ready_and_game_state():
    lobby = LobbyState(code="LOBBY1", ready_players={"Alice"}, game_state=MagicMock())
    reset_lobby(lobby)
    assert not lobby.ready_players
    assert lobby.game_state is None