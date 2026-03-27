import unittest
from unittest.mock import MagicMock, patch
from app.data.repository import get_all_cards, create_user

class TestUserAndCards(unittest.TestCase):

    @patch('app.data.repository.get_connection')
    def test_get_all_cards(self, mock_get_conn):
        """Tests fetching all cards returns a list of dictionaries."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        fake_cards = [{'id': 1, 'name': 'Dragon'}, {'id': 2, 'name': 'Goblin'}]
        mock_cursor.fetchall.return_value = fake_cards

        result = get_all_cards()

        self.assertEqual(result, fake_cards)
        mock_cursor.execute.assert_called_once_with("SELECT * FROM cards")
        mock_conn.close.assert_called_once()

    @patch('app.data.repository.get_connection')
    def test_create_user(self, mock_get_conn):
        """Tests that user creation executes the INSERT and commits."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        create_user("test_user", "secure_pass123")

        expected_query = "INSERT INTO users (username, password) VALUES (%s, %s)"
        mock_cursor.execute.assert_called_once_with(expected_query, ("test_user", "secure_pass123"))
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

if __name__ == '__main__':
    unittest.main()