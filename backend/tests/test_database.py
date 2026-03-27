import unittest
from unittest.mock import MagicMock, patch
from mysql.connector import Error
from app.data import database as db_manager

class TestDatabase(unittest.TestCase):

    @patch('app.data.database.get_connection')
    def test_execute_query_fetch_success(self, mock_get_conn):
        """Test execute_query returns data when fetch=True"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        expected_data = [{'id': 1, 'name': 'Ace of Spades'}]
        mock_cursor.fetchall.return_value = expected_data
        
        result = db_manager.execute_query("SELECT * FROM cards", fetch=True)
        
        mock_cursor.execute.assert_called_once_with("SELECT * FROM cards", ())
        self.assertEqual(result, expected_data)
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch('app.data.database.get_connection')
    def test_execute_query_commit(self, mock_get_conn):
        """Test execute_query commits changes when fetch=False"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        db_manager.execute_query("INSERT INTO cards (name) VALUES (%s)", params=("King",))
        
        mock_conn.commit.assert_called_once()
        mock_conn.rollback.assert_not_called()

    @patch('app.data.database.get_connection')
    def test_execute_query_error_handling(self, mock_get_conn):
        """Test execute_query rolls back on database error"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        mock_cursor.execute.side_effect = Error("Database error")
        
        db_manager.execute_query("DELETE FROM cards")
        
        mock_conn.rollback.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch('app.data.database.get_connection')
    def test_execute_query_with_params(self, mock_get_conn):
        cursor = MagicMock()
        conn = MagicMock()
        conn.cursor.return_value = cursor

        mock_get_conn.return_value = conn

        db_manager.execute_query("SELECT * FROM users WHERE id=%s", (1,))

        cursor.execute.assert_called_once_with(
            "SELECT * FROM users WHERE id=%s", (1,)
        )

    @patch("app.data.database._get_pool")
    def test_get_connection(self, mock_get_pool):
        mock_conn = MagicMock()
        mock_pool = MagicMock()
        mock_pool.get_connection.return_value = mock_conn

        mock_get_pool.return_value = mock_pool

        conn = db_manager.get_connection()

        assert conn == mock_conn
        mock_pool.get_connection.assert_called_once()
if __name__ == '__main__':
    unittest.main()