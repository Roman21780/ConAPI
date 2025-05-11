from django.test import TestCase
from wb_api.client import WildberriesClient
from unittest.mock import patch
import json


class ProductsTestCase(TestCase):
    @patch('wb_api.client.base.requests.Session.request')
    def test_get_products(self, mock_request):
        mock_data = {
            "items": [{
                "productId": "123",
                "name": "Test Product",
                # ... другие поля
            }],
            "total": 1
        }
        mock_request.return_value.status_code = 200
        mock_request.return_value.json.return_value = mock_data

        client = WildberriesClient()
        response = client.get_prds()

        self.assertTrue(response.success)
        self.assertEqual(len(response.data['items']), 1)
        self.assertEqual(response.data['items'][0]['product_id'], "123")

    @patch('wb_api.client.base.requests.Session.request')
    def test_get_product_not_found(self, mock_request):
        mock_request.return_value.status_code = 404

        client = WildberriesClient()
        response = client.get_prd("nonexistent_id")

        self.assertFalse(response.success)
        self.assertIn("API error", response.error)