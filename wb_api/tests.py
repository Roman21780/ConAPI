from django.test import TestCase
from unittest.mock import patch, MagicMock
import requests  # Добавляем импорт requests

from .client.base import WBClientBase
from .client.client import WBClient
from wb_api.models import WBResponse


class AuthTests(TestCase):
    def setUp(self):
        self.client = WBClient(base_url="https://api.test", api_key="test_key")

    @patch('requests.Session.request')
    def test_valid_token(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"valid": True}
        mock_request.return_value = mock_response

        response = self.client.check_creds("valid_token")
        self.assertTrue(response.success)
        self.assertEqual(response.data, {"valid": True})

    @patch('requests.Session.request')
    def test_invalid_token(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_request.return_value = mock_response

        response = self.client.check_creds("invalid_token")
        self.assertFalse(response.success)
        self.assertEqual(response.error, "Unauthorized")


class CategoryTests(TestCase):
    def setUp(self):
        self.client = WBClient(base_url="https://api.test", api_key="test_key")
        self.test_categories = {
            "items": [{"id": 1, "name": "Test Category"}],
            "total": 1
        }

    @patch('requests.Session.request')
    def test_get_categories(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.test_categories
        mock_request.return_value = mock_response

        response = self.client.get_categories()
        self.assertTrue(response.success)
        self.assertEqual(response.data, self.test_categories)


class ProductTests(TestCase):
    def setUp(self):
        self.client = WBClient(base_url="https://api.test", api_key="test_key")
        self.test_product = {"id": "12345", "name": "Test Product"}

    @patch('requests.Session.request')
    def test_get_products(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"items": [self.test_product], "total": 1}
        mock_request.return_value = mock_response

        response = self.client.get_products()
        self.assertTrue(response.success)
        self.assertIn(self.test_product, response.data["items"])

    @patch('requests.Session.request')
    def test_update_product(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.test_product
        mock_request.return_value = mock_response

        response = self.client.update_product("12345", {"price": 1099})
        self.assertTrue(response.success)
        self.assertEqual(response.data, self.test_product)


class OrderTests(TestCase):
    def setUp(self):
        self.client = WBClient(base_url="https://api.test", api_key="test_key")
        self.test_order = {"id": "54321", "status": "processed"}

    @patch('requests.Session.request')
    def test_get_orders(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"items": [self.test_order], "total": 1}
        mock_request.return_value = mock_response

        response = self.client.get_orders()
        self.assertTrue(response.success)
        self.assertIn(self.test_order, response.data["items"])


class ErrorHandlingTests(TestCase):
    def setUp(self):
        self.client = WBClientBase(token="test_key")

    @patch('requests.Session.request')
    def test_connection_error(self, mock_request):
        mock_request.side_effect = requests.exceptions.ConnectionError("Connection failed")

        response = self.client._request('GET', '/test')
        self.assertFalse(response.success)
        self.assertEqual(response.error, "Request failed: Connection failed")

    @patch('requests.Session.request')
    def test_api_error_handling(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_request.return_value = mock_response

        response = self.client._request('GET', '/invalid')
        self.assertFalse(response.success)
        self.assertEqual(response.error, "Not Found")


class IntegrationTests(TestCase):
    def setUp(self):
        self.client = WBClientBase(token="test_key")

    @patch('wb_api.client.base.WBClientBase._request')
    def test_full_workflow(self, mock_request):
        # Настройка моков для каждого вызова
        mock_request.side_effect = [
            # Ответ для check_creds
            WBResponse(success=True, data={"valid": True}, error=None),
            # Ответ для get_products
            WBResponse(success=True, data={"items": [{"id": "12345"}], "total": 1}, error=None),
            # Ответ для get_orders
            WBResponse(success=True, data={"items": [{"id": "54321"}], "total": 1}, error=None)
        ]

        # Тестируем check_creds
        auth_response = self.client.check_creds("test_token")
        self.assertTrue(auth_response.success)

        # Проверяем, что был вызван правильный endpoint
        mock_request.assert_any_call('GET', '/v1/auth/test')

        # Тестируем get_products
        products_response = self.client.get_products()
        self.assertTrue(products_response.success)
        self.assertEqual(len(products_response.data["items"]), 1)

        # Тестируем get_orders
        orders_response = self.client.get_orders()
        self.assertTrue(orders_response.success)
        self.assertEqual(len(orders_response.data["items"]), 1)