import unittest
from unittest.mock import MagicMock, patch

from app.data.seed import seed_database

class TestDatabaseSeeding(unittest.TestCase):

    @patch('app.data.seed.get_connection')
    def test_seed_database_success(self, mock_get_conn):
        """Test that seed_database calls executemany for both cards and users."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        seed_database()

        self.assertEqual(mock_cursor.executemany.call_count, 2)

        card_query = "INSERT INTO cards (card_name, card_type, card_detail) VALUES (%s, %s, %s)"
        first_call_args = mock_cursor.executemany.call_args_list[0]
        self.assertEqual(first_call_args[0][0], card_query)
        self.assertEqual(len(first_call_args[0][1]), 4) 

        user_query = "INSERT INTO users (username, password, total_games_played, total_wins, total_losses) VALUES (%s, %s, %s, %s, %s)"
        second_call_args = mock_cursor.executemany.call_args_list[1]
        self.assertEqual(second_call_args[0][0], user_query)
        self.assertEqual(len(second_call_args[0][1]), 3) 

        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch('app.data.seed.get_connection')
    def test_seed_database_error(self, mock_get_conn):
        """Test that if seeding fails, rollback is called."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        mock_cursor.executemany.side_effect = [None, Exception("User table full")]

        seed_database()

        mock_conn.rollback.assert_called_once()
        mock_conn.close.assert_called_once()

if __name__ == '__main__':
    unittest.main()