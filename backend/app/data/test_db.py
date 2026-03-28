import unittest
from unittest.mock import MagicMock, patch
from app.data.repository import get_all_cards


class TestDatabase(unittest.TestCase):
    @patch("app.data.repository.get_connection")
    def test_get_all_cards_returns_list(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            {"card_id": 1, "card_name": "Test Card"},
        ]

        results = get_all_cards()

        self.assertIsInstance(results, list)
        self.assertIn("card_name", results[0])


if __name__ == "__main__":
    unittest.main()
