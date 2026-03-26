import pytest
from unittest.mock import MagicMock, patch
from app.data.models import save_game_result, get_recent_results

@pytest.fixture
def mock_db():
    """Fixture to mock the database connection and cursor."""
    with patch("app.data.models.get_connection") as mock_get_conn:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        yield mock_conn, mock_cursor


def test_save_game_result_success(mock_db):
    mock_conn, mock_cursor = mock_db
    mock_cursor.fetchone.return_value = ("games",)

    save_game_result("Alice")

    mock_cursor.execute.assert_any_call("SHOW TABLES LIKE %s", ("games",))
    mock_cursor.execute.assert_any_call(
        "INSERT INTO games (status, winner) VALUES (%s, %s)", 
        ("completed", "Alice")
    )
    mock_conn.commit.assert_called_once()
    mock_cursor.close.assert_called_once()

def test_save_game_result_no_table(mock_db):
    mock_conn, mock_cursor = mock_db
    mock_cursor.fetchone.return_value = None

    save_game_result("Alice")

    mock_conn.rollback.assert_called_once()
    assert mock_cursor.execute.call_count == 1 


def test_get_recent_results_success(mock_db):
    _, mock_cursor = mock_db
    mock_cursor.fetchone.return_value = ("games",)
    mock_cursor.fetchall.return_value = [
        {"id": 1, "winner": "Alice", "played_at": "2024-01-01"},
        {"id": 2, "winner": "Bob", "played_at": "2024-01-02"}
    ]

    results = get_recent_results(limit=5)

    assert len(results) == 2
    assert results[0]["winner"] == "Alice"
    mock_cursor.execute.assert_any_call(mock_cursor.execute.call_args_list[1][0][0], (5,))

def test_get_recent_results_empty_if_no_table(mock_db):
    _, mock_cursor = mock_db
    mock_cursor.fetchone.return_value = None

    results = get_recent_results()

    assert results == []
    assert mock_cursor.execute.call_count == 1