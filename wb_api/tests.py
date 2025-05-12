import json
from datetime import datetime, timedelta
from unittest.mock import patch, Mock
from django.test import TestCase, override_settings
from django.utils import timezone
from wb_api.client import WildberriesClient, WBResponse
from wb_api.models import APICache
from wb_api.exceptions import WBAuthError
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()


class WBBaseTestCase(TestCase):
    def setUp(self):
        APICache.objects.all().delete()
        self.client = WildberriesClient(token='test_token')
        self.test_product = {
            "product_id": "12345",
            "name": "Test Product",
            "prices": [{"price": 999, "currency": "RUB"}],
            "stocks": [{"warehouse_id": 1, "amount": 100}]
        }
        self.test_order = {
            "order_id": "ORD-123",
            "status": "completed",
            "items": [{"product_id": "12345", "quantity": 2}]
        }
        self.test_category = {
            "category_id": 123,
            "name": "Test Category",
            "parent_id": None
        }

        # Очищаем кэш перед каждым тестом
        APICache.objects.all().delete()

    def tearDown(self):
        # Дополнительная очистка после тестов
        APICache.objects.all().delete()


class AuthTests(WBBaseTestCase):
    @patch('wb_api.client.wildberries.WildberriesClient._request')
    def test_valid_token(self, mock_request):
        # Мок возвращает WBResponse
        mock_request.return_value = WBResponse(
            success=True,
            data={},
            error=None,
            status_code=200
        )

        response = self.client.check_creds("valid_token")
        self.assertTrue(response.success)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.error)

    @patch('wb_api.client.wildberries.WildberriesClient._request')
    def test_invalid_token(self, mock_request):
        # Мок возвращает WBResponse с ошибкой
        mock_request.return_value = WBResponse(
            success=False,
            data=None,
            error="Invalid token",
            status_code=401
        )

        response = self.client.check_creds("invalid_token")
        self.assertFalse(response.success)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.error, "Invalid token")


class ProductTests(WBBaseTestCase):
    @patch('wb_api.client.WBClientBase._request')
    def test_get_products(self, mock_request):
        mock_request.return_value = WBResponse(
            success=True,  # Убедитесь, что здесь True
            data={"items": [self.test_product], "total": 1},
            error=None,
            status_code=200
        )
        response = self.client.get_prds()
        self.assertTrue(response.success)
        self.assertEqual(response.status_code, 200)

    @patch('wb_api.client.WBClientBase._request')
    def test_get_product_details(self, mock_request):
        mock_request.return_value = WBResponse(
            success=True,
            data=self.test_product,
            error=None,
            status_code=200
        )

        response = self.client.get_prd("12345")
        self.assertTrue(response.success)
        self.assertEqual(response.data['name'], "Test Product")
        self.assertEqual(response.data['prices'][0]['price'], 999)

    @patch('wb_api.client.WBClientBase._request')
    def test_update_product(self, mock_request):
        mock_request.return_value = WBResponse(
            success=True,
            data={"updated": True},
            error=None,
            status_code=200
        )

        # Используем WBResponse вместо словаря
        test_response = WBResponse(
            success=True,
            data=self.test_product,
            error=None,
            status_code=200
        )

        APICache.set_cached_response(
            endpoint="get_prd:12345",
            response=test_response,  # Передаем WBResponse
            ttl=3600
        )

        response = self.client.set_prd("12345", {"price": 1099})
        self.assertTrue(response.success)
        self.assertEqual(response.status_code, 200)


class OrderTests(WBBaseTestCase):
    @patch('wb_api.client.WBClientBase._request')
    def test_get_orders(self, mock_request):
        mock_request.return_value = WBResponse(
            success=True,
            data={"items": [self.test_order], "total": 1},
            error=None,
            status_code=200
        )

        response = self.client.get_orders()
        self.assertTrue(response.success)
        self.assertEqual(response.data['items'][0]['order_id'], "ORD-123")


class CategoryTests(WBBaseTestCase):
    @patch('wb_api.client.WBClientBase._request')
    def test_get_categories(self, mock_request):
        mock_request.return_value = WBResponse(
            success=True,
            data={"items": [self.test_category], "total": 1},
            error=None,
            status_code=200
        )

        response = self.client.get_categories()
        self.assertTrue(response.success)
        self.assertEqual(response.data['items'][0]['name'], "Test Category")


class CacheTests(WBBaseTestCase):
    def test_cache_workflow(self):
        # Явная очистка перед тестом
        APICache.objects.all().delete()

        # Проверяем пустой кэш
        self.assertEqual(APICache.objects.count(), 0)

        # Добавляем тестовые данные
        test_response = WBResponse(
            success=True,
            data={"test": "value"},
            error=None,
            status_code=200
        )

        APICache.set_cached_response(
            endpoint="test_endpoint",
            response=test_response,
            params={"param": "value"},
            ttl=60
        )

        # Проверяем наличие записи
        self.assertEqual(APICache.objects.count(), 1)

        # Получаем данные из кэша
        cached = APICache.get_cached_response("test_endpoint", {"param": "value"})
        self.assertIsNotNone(cached)
        self.assertEqual(cached['data']['test'], "value")

        # Очищаем кэш
        APICache.objects.all().delete()
        self.assertEqual(APICache.objects.count(), 0)


class ErrorHandlingTests(WBBaseTestCase):
    @patch('wb_api.client.WBClientBase._request')
    def test_connection_error(self, mock_request):
        mock_request.return_value = WBResponse(
            success=False,
            data=None,
            error="Connection error",
            status_code=503
        )

        response = self.client._request('GET', '/test')
        self.assertFalse(response.success)
        self.assertEqual(response.error, "Connection error")

    @patch('wb_api.client.WBClientBase._request')
    def test_api_error_handling(self, mock_request):
        mock_request.return_value = WBResponse(
            success=False,
            data=None,
            error="Invalid request",
            status_code=400
        )

        response = self.client._request('GET', '/invalid')
        self.assertFalse(response.success)
        self.assertEqual(response.status_code, 400)


class IntegrationTests(WBBaseTestCase):
    @patch('wb_api.client.WildberriesClient._request')
    def test_full_workflow(self, mock_request):
        # Настраиваем возвращаемые WBResponse для каждого вызова
        mock_request.side_effect = [
            # check_creds
            WBResponse(True, {}, None, 200),
            # get_prds
            WBResponse(True, {"items": [self.test_product]}, None, 200),
            # get_prd
            WBResponse(True, self.test_product, None, 200),
            # set_prd
            WBResponse(True, {"updated": True}, None, 200),
            # get_orders
            WBResponse(True, {"items": [self.test_order]}, None, 200)
        ]

        # 1. Авторизация
        auth_response = self.client.check_creds("test_token")
        self.assertTrue(auth_response.success)

        # 2. Получение товаров
        products_response = self.client.get_prds()
        self.assertTrue(products_response.success)
        self.assertEqual(len(products_response.data['items']), 1)

        # 3. Получение деталей товара
        product_response = self.client.get_prd("12345")
        self.assertEqual(product_response.data['name'], "Test Product")

        # 4. Обновление товара
        update_response = self.client.set_prd("12345", {"price": 1099})
        self.assertTrue(update_response.success)

        # 5. Получение заказов
        orders_response = self.client.get_orders()
        self.assertEqual(orders_response.data['items'][0]['order_id'], "ORD-123")

        # Проверяем количество вызовов API
        self.assertEqual(mock_request.call_count, 5)
