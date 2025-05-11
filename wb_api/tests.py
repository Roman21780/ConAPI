from django.test import TestCase

# Create your tests here.

from django.test import TestCase, override_settings
from unittest.mock import patch, Mock
from wb_api.client import WildberriesClient, WBResponse
from wb_api.models import APICache
from wb_api.exceptions import WBAuthError
import json
from datetime import datetime, timedelta
from django.utils import timezone


class WBClientBaseTestCase(TestCase):
    def setUp(self):
        self.client = WildberriesClient(token='test_token')
        self.valid_product_id = '12345'
        self.valid_order_id = 'ORD-54321'
        self.valid_category_id = 123

    @override_settings(WB_API_URL='https://dev.wildberries.ru/api',
                       WB_API_TOKEN='test_token')
    def test_client_initialization(self):
        client = WildberriesClient()
        self.assertEqual(client.base_url, 'https://dev.wildberries.ru/api')
        self.assertEqual(client.token, 'test_token')

    @patch('wb_api.client.WBClientBase._request')
    def test_check_creds_valid(self, mock_request):
        mock_request.return_value = WBResponse(True, {}, None, 200)
        response = self.client.check_creds('valid_token')
        self.assertTrue(response.success)
        self.assertEqual(response.error, None)

    @patch('wb_api.client.WBClientBase._request')
    def test_check_creds_invalid(self, mock_request):
        mock_request.return_value = WBResponse(False, None, "Invalid token", 401)
        response = self.client.check_creds('invalid_token')
        self.assertFalse(response.success)
        self.assertEqual(response.error, "Invalid token")


class WBProductsClientTestCase(TestCase):
    def setUp(self):
        self.client = WildberriesClient(token='test_token')
        self.sample_product = {
            "product_id": "12345",
            "name": "Test Product",
            "prices": [{"price": 999, "currency": "RUB"}],
            "stocks": [{"warehouse_id": 1, "amount": 100}]
        }

    @patch('wb_api.client.WBClientBase._request')
    def test_get_prds_success(self, mock_request):
        mock_request.return_value = WBResponse(
            True,
            {"items": [self.sample_product], "total": 1},
            None,
            200
        )
        response = self.client.get_prds()
        self.assertTrue(response.success)
        self.assertEqual(len(response.data['items']), 1)
        self.assertEqual(response.data['items'][0]['product_id'], "12345")

    @patch('wb_api.client.WBClientBase._request')
    def test_get_prd_success(self, mock_request):
        mock_request.return_value = WBResponse(True, self.sample_product, None, 200)
        response = self.client.get_prd("12345")
        self.assertTrue(response.success)
        self.assertEqual(response.data['name'], "Test Product")

    @patch('wb_api.client.WBClientBase._request')
    def test_set_prd_success(self, mock_request):
        mock_request.return_value = WBResponse(True, {"updated": True}, None, 200)
        response = self.client.set_prd("12345", {"price": 1099})
        self.assertTrue(response.success)
        self.assertTrue(response.data['updated'])

    @patch('wb_api.client.WBClientBase._request')
    def test_get_comission_success(self, mock_request):
        mock_request.return_value = WBResponse(True, {"commission": 15}, None, 200)
        response = self.client.get_comission("12345")
        self.assertTrue(response.success)
        self.assertEqual(response.data['commission'], 15)


class WBCacheTestCase(TestCase):
    def setUp(self):
        self.test_data = {"key": "value"}
        self.cache_key = "test_endpoint:{}".format(json.dumps({"param": "value"}))

    def test_cache_workflow(self):
        # Проверяем что кэш пустой
        self.assertIsNone(APICache.get_cached_response("test_endpoint", {"param": "value"}))

        # Сохраняем данные в кэш
        APICache.set_cached_response(
            endpoint="test_endpoint",
            response=self.test_data,
            params={"param": "value"},
            ttl=60
        )

        # Проверяем что данные есть в кэше
        cached = APICache.get_cached_response("test_endpoint", {"param": "value"})
        self.assertEqual(cached, self.test_data)

        # Очищаем кэш
        APICache.clear_expired()
        APICache.objects.filter(endpoint=self.cache_key).delete()
        self.assertIsNone(APICache.get_cached_response("test_endpoint", {"param": "value"}))


class WBErrorHandlingTestCase(TestCase):
    @patch('requests.Session.request')
    def test_connection_error(self, mock_request):
        mock_request.side_effect = ConnectionError("Connection failed")
        client = WildberriesClient()
        response = client._request('GET', '/test')
        self.assertFalse(response.success)
        self.assertEqual(response.error, "Connection error after multiple retries")

    @patch('requests.Session.request')
    def test_invalid_json_response(self, mock_request):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_request.return_value = mock_response

        client = WildberriesClient()
        response = client._request('GET', '/test')
        self.assertFalse(response.success)
        self.assertIn("Invalid JSON", response.error)

    @patch('requests.Session.request')
    def test_api_error_parsing(self, mock_request):
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = '{"error": {"message": "Invalid request"}}'
        mock_response.json.return_value = {"error": {"message": "Invalid request"}}
        mock_request.return_value = mock_response

        client = WildberriesClient()
        response = client._request('GET', '/test')
        self.assertFalse(response.success)
        self.assertEqual(response.error, "Invalid request")


class WBIntegrationTestCase(TestCase):
    @patch('wb_api.client.WBClientBase._request')
    def test_full_workflow(self, mock_request):
        # Мокируем все вызовы API
        mock_request.side_effect = [
            # check_creds
            WBResponse(True, {}, None, 200),
            # get_prds
            WBResponse(True, {"items": [{"product_id": "123"}]}, None, 200),
            # get_prd
            WBResponse(True, {"product_id": "123", "name": "Test"}, None, 200),
            # set_prd
            WBResponse(True, {"success": True}, None, 200),
            # get_comission
            WBResponse(True, {"commission": 10}, None, 200)
        ]

        client = WildberriesClient()

        # 1. Проверяем токен
        auth = client.check_creds('test_token')
        self.assertTrue(auth.success)

        # 2. Получаем список товаров
        products = client.get_prds()
        self.assertTrue(products.success)
        self.assertEqual(len(products.data['items']), 1)

        # 3. Получаем конкретный товар
        product = client.get_prd("123")
        self.assertTrue(product.success)
        self.assertEqual(product.data['name'], "Test")

        # 4. Обновляем товар
        update = client.set_prd("123", {"price": 999})
        self.assertTrue(update.success)

        # 5. Проверяем комиссию
        commission = client.get_comission("123")
        self.assertTrue(commission.success)
        self.assertEqual(commission.data['commission'], 10)

    def test_cache_invalidation(self):
        # Добавляем тестовые данные в кэш
        APICache.objects.create(
            endpoint="get_prd:123",
            response=json.dumps({"product_id": "123"}),
            expires_at=timezone.now() + timedelta(hours=1)
        )

        # Проверяем что данные есть в кэше
        self.assertIsNotNone(APICache.get_cached_response("get_prd", {"123"}))

        # Инвалидируем кэш
        client = WildberriesClient()
        client.invalidate_cache("get_prd", {"123"})

        # Проверяем что данные удалены
        self.assertIsNone(APICache.get_cached_response("get_prd", {"123"}))