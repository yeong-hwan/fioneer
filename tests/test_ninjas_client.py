import unittest
from unittest.mock import patch, MagicMock
from fioneer.ninjas.ninjas_client import NinjasClient

class TestNinjasClient(unittest.TestCase):
    def setUp(self):
        self.client = NinjasClient()
        
    @patch('requests.get')
    def test_get_earnings_transcript(self, mock_get):
        # Mock response setup
        mock_response = MagicMock()
        mock_response.json.return_value = {"transcript": "test data"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Test parameters
        symbol = "AAPL"
        year = 2023
        quarter = 4

        # Execute test
        result = self.client.get_earnings_transcript(symbol, year, quarter)

        # Verify API call
        mock_get.assert_called_once_with(
            f"{NinjasClient.BASE_URL}/earningstranscript",
            params={"ticker": symbol, "year": year, "quarter": quarter},
            headers={"X-Api-Key": self.client.ninja_api_key}
        )

        # Verify result
        self.assertEqual(result, {"transcript": "test data"})
