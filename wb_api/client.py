import requests
from django.conf import settings
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass
import json
from urllib.parse import urlencode
from datetime import datetime, timedelta
import logging
from datetime import time

logger = logging.getLogger(__name__)


@dataclass
class WBResponse:
    def __init__(self, success, data, error, status_code):
        self.success = success
        self.data = data
        self.error = error
        self.status_code = status_code  # Обязательное поле


class WBClientBase:
    BASE_URL = 'https://suppliers-api.wildberries.ru'
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY = 1

    def __init__(self, token: Optional[str] = None):
        self.token = token or getattr(settings, 'WB_API_TOKEN', None)
        if not self.token:
            raise ValueError("Wildberries API token is not configured")

        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.session.timeout = self.DEFAULT_TIMEOUT

    def _request(
            self,
            method: str,
            endpoint: str,
            params: Optional[Dict] = None,
            data: Optional[Dict] = None,
            use_cache: bool = False
    ) -> WBResponse:
        """
        Базовый метод для выполнения запросов к API Wildberries
        """
        url = f"{self.BASE_URL}{endpoint}"

        for attempt in range(self.MAX_RETRIES):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data
                )

                logger.debug(f"Request: {method} {url}")
                logger.debug(f"Params: {params}")
                logger.debug(f"Status: {response.status_code}")
                logger.debug(f"Response: {response.text[:200]}...")

                if response.status_code == 401:
                    return WBResponse(
                        success=False,
                        data=None,
                        error="Invalid API token",
                        status_code=401
                    )

                if response.status_code >= 400:
                    error_msg = self._parse_error(response)
                    return WBResponse(
                        success=False,
                        data=None,
                        error=error_msg,
                        status_code=response.status_code
                    )

                try:
                    response_data = response.json()
                except ValueError as e:
                    return WBResponse(
                        success=False,
                        data=None,
                        error=f"Invalid JSON response: {str(e)}",
                        status_code=500
                    )

                return WBResponse(
                    success=True,
                    data=response_data,
                    error=None,
                    status_code=response.status_code
                )

            except requests.exceptions.ConnectionError as e:
                if attempt == self.MAX_RETRIES - 1:
                    return WBResponse(
                        success=False,
                        data=None,
                        error="Connection error after multiple retries",
                        status_code=503
                    )
                time.sleep(self.RETRY_DELAY)

            except Exception as e:
                logger.error(f"API request failed: {str(e)}")
                if attempt == self.MAX_RETRIES - 1:
                    return WBResponse(
                        success=False,
                        data=None,
                        error=str(e),
                        status_code=500
                    )
                time.sleep(self.RETRY_DELAY)

    def _parse_error(self, response: requests.Response) -> str:
        """Парсинг ошибок из ответа API"""
        try:
            error_data = response.json()
            if isinstance(error_data, dict):
                return error_data.get('error', {}).get('message', response.text)
            return response.text
        except ValueError:
            return response.text


class WBProductsClient(WBClientBase):
    def get_products(self, filter: Optional[Dict] = None) -> WBResponse:
        """Получение списка товаров"""
        return self._request('GET', '/api/v1/products', params=filter)

    def get_product(self, product_id: str) -> WBResponse:
        """Получение информации о конкретном товаре"""
        return self._request('GET', f'/api/v1/products/{product_id}')

    def update_product(self, product_id: str, data: Dict) -> WBResponse:
        """Обновление информации о товаре"""
        return self._request('PATCH', f'/api/v1/products/{product_id}', data=data)


class WBOrdersClient(WBClientBase):
    def get_orders(self, filter: Optional[Dict] = None) -> WBResponse:
        """Получение списка заказов"""
        return self._request('GET', '/api/v1/orders', params=filter)


class WBCategoriesClient(WBClientBase):
    def get_categories(self) -> WBResponse:
        """Получение списка категорий"""
        return self._request('GET', '/api/v1/categories')


class WildberriesClient(WBProductsClient, WBOrdersClient, WBCategoriesClient):
    """Основной клиент для работы со всеми методами API Wildberries"""

    def check_auth(self) -> WBResponse:
        """Проверка авторизации"""
        return self._request('GET', '/api/v1/auth/test')