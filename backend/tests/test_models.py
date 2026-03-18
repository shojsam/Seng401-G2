#### NEEDS WORK
import unittest
from unittest.mock import MagicMock, patch
# Replace 'your_app' with the actual name of your package/folder
from app.data.models import save_game_result, get_recent_results

class TestGameResults(unittest.TestCase):

    @patch('app.data.models.save_game_result.db_pool.get_connection')
    def test_save_game_result_success(self, mock_get_conn):
        """Test that a game result is saved and committed correctly."""
        # Setup Mocks
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Execute
        save_game_result("Alice")

        # Assertions
        mock_cursor.execute.assert_called_once_with(
            "INSERT INTO game_results (winner) VALUES (%s)", ("Alice",)
        )
        mock_conn.commit.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch('app.data.models.save_game_result.db_pool.get_connection')
    def test_save_game_result_failure(self, mock_get_conn):
        """Test that a database error triggers a rollback."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Simulate an exception during execution
        mock_cursor.execute.side_effect = Exception("DB Connection Lost")

        save_game_result("Bob")

        # Assertions
        mock_conn.rollback.assert_called_once()
        # Finally block should still close connections
        mock_conn.close.assert_called_once()

    @patch('app.data.models.get_recent_results.db_pool.get_connection')
    def test_get_recent_results(self, mock_get_conn):
        """Test fetching results returns the expected dictionary list."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mocking the dictionary=True return value
        expected_data = [{"id": 1, "winner": "Alice", "played_at": "2023-01-01"}]
        mock_cursor.fetchall.return_value = expected_data

        results = get_recent_results(limit=5)

        # Assertions
        mock_cursor.execute.assert_called_once_with(
            "SELECT * FROM game_results ORDER BY played_at DESC LIMIT %s", (5,)
        )
        self.assertEqual(results, expected_data)
        mock_conn.close.assert_called_once()

if __name__ == '__main__':
    unittest.main()