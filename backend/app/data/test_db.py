import unittest
from repository import get_all_cards

class TestDatabase(unittest.TestCase):
    def test_get_all_cards_returns_list(self):
        # Act
        results = get_all_cards()
    
        # Assert
        self.assertIsInstance(results, list)
        if len(results) > 0:
            self.assertIn('card_name', results[0])

if __name__ == '__main__':
    unittest.main()