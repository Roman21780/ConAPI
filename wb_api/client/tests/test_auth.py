from django.test import TestCase
from wb_api.client import WildberriesClient
from unittest.mock import patch


class AuthTestCase(TestCase):
    @patch('wb_api.client.base.requests.Session.request')
    def test_valid_token(self, mock_request):
        mock_request.return_value.status_code = 200
        client = WildberriesClient(token="valid_token")
        response = client.check_creds("valid_token")
        self.assertTrue(response.success)
        self.assertTrue(response.data['valid'])

    @patch('wb_api.client.base.requests.Session.request')
    def test_invalid_token(self, mock_request):
        mock_request.return_value.status_code = 401
        client = WildberriesClient(token="invalid_token")
        response = client.check_creds("invalid_token")
        self.assertFalse(response.success)
        self.assertEqual(response.error, "Invalid API token")