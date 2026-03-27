import pytest
from unittest.mock import MagicMock, patch, mock_open

from app.data.seed import (
    initialize_database,
    ensure_cards_hover_column,
    seed_database,
)

def make_mock_connection(cursor_mock):
    conn = MagicMock()
    conn.cursor.return_value = cursor_mock
    conn.database = "test_db"
    return conn


@patch("app.data.seed.get_connection")
def test_initialize_database_already_initialized(mock_get_conn):
    cursor = MagicMock()
    cursor.fetchall.return_value = [
        ("users",),
        ("games",),
        ("game_players",),
        ("cards",),
        ("lobbies",),
        ("lobby_players",),
    ]

    conn = make_mock_connection(cursor)
    mock_get_conn.return_value = conn

    initialize_database()

    cursor.execute.assert_called_with("SHOW TABLES")
    conn.commit.assert_not_called()


@patch("app.data.seed.get_connection")
@patch("pathlib.Path.read_text")
def test_initialize_database_runs_schema(mock_read_text, mock_get_conn):
    cursor = MagicMock()
    cursor.fetchall.return_value = [("users",)]

    conn = make_mock_connection(cursor)
    mock_get_conn.return_value = conn

    mock_read_text.return_value = """
        CREATE TABLE test1 (id INT);
        CREATE TABLE test2 (id INT);
    """

    initialize_database()

    assert cursor.execute.call_count >= 3 
    conn.commit.assert_called_once()



@patch("app.data.seed.get_connection")
def test_hover_column_already_exists(mock_get_conn):
    cursor = MagicMock()
    cursor.fetchone.return_value = ("hover",)

    conn = make_mock_connection(cursor)
    mock_get_conn.return_value = conn

    ensure_cards_hover_column()

    cursor.execute.assert_called_once_with(
        "SHOW COLUMNS FROM cards LIKE 'hover'"
    )
    conn.commit.assert_not_called()


@patch("app.data.seed.get_connection")
def test_hover_column_added(mock_get_conn):
    cursor = MagicMock()
    cursor.fetchone.return_value = None

    conn = make_mock_connection(cursor)
    mock_get_conn.return_value = conn

    ensure_cards_hover_column()

    assert cursor.execute.call_count == 2
    conn.commit.assert_called_once()



@patch("app.data.seed.get_connection")
def test_seed_database_with_existing_users(mock_get_conn):
    cursor = MagicMock()

    cursor.fetchone.return_value = (5,) 

    conn = make_mock_connection(cursor)
    mock_get_conn.return_value = conn

    seed_database()

    cursor.execute.assert_any_call("DELETE FROM cards")
    insert_calls = [
        call for call in cursor.executemany.call_args_list
        if "INSERT INTO users" in str(call)
    ]
    assert not insert_calls

    conn.commit.assert_called_once()


@patch("app.data.seed.get_connection")
def test_seed_database_with_no_users(mock_get_conn):
    cursor = MagicMock()

    cursor.fetchone.return_value = (0,)

    conn = make_mock_connection(cursor)
    mock_get_conn.return_value = conn

    seed_database()

    assert any(
        "INSERT INTO users" in str(call)
        for call in cursor.executemany.call_args_list
    )

    conn.commit.assert_called_once()


@patch("app.data.seed.get_connection")
def test_seed_database_rollback_on_error(mock_get_conn):
    cursor = MagicMock()

    cursor.execute.side_effect = Exception("DB error")

    conn = make_mock_connection(cursor)
    mock_get_conn.return_value = conn

    with pytest.raises(Exception):
        seed_database()

    conn.rollback.assert_called_once()