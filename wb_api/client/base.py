import requests
from django.conf import settings
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass
import json
import time
from urllib.parse import urlencode

from wb_api.exceptions import WBAuthError, WBAPIError
from wb_api.models import APICache, WBAPIStats


@dataclass
class WBResponse:
    success: bool
    data: any
    error: Optional[str]
    status_code: int  # Обязательное поле

    def __post_init__(self):
        if not hasattr(self, 'status_code'):
            raise ValueError("status_code is required")

class WBClientBase:
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY = 1

    def __init__(self, token: str):
        self.token = token
        self.session = requests.Session()  # Инициализация сессии
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        })

    def _request(self, method, endpoint, **kwargs):
        import requests

        headers = {
            'Authorization': self.token,
            'Content-Type': 'application/json'
        }
        headers.update(kwargs.get('headers', {}))

        try:
            response = requests.request(
                method,
                f"{self.base_url}{endpoint}",
                headers=headers,
                **kwargs
            )
            return response
        except Exception as e:
            return WBResponse(
                success=False,
                data=None,
                error=str(e),
                status_code=500
            )

    def _invalidate_cache(self, cache_key: str):
        """Инвалидирует кэш по ключу"""
        from .models.cache import ClientAPICache  # Отложенный импорт чтобы избежать циклических зависимостей
        ClientAPICache.objects.filter(endpoint__startswith=cache_key).delete()

    def _generate_cache_key(self, endpoint: str, params: Optional[Dict] = None) -> str:
        """Генерация ключа кэша на основе endpoint и параметров"""
        if not params:
            return endpoint
        return f"{endpoint}?{urlencode(sorted(params.items()))}"

    def _parse_error(self, response: requests.Response) -> str:
        """Парсинг ошибок API Wildberries"""
        try:
            error_data = response.json()
            if isinstance(error_data, dict):
                return error_data.get('error', {}).get('message', response.text)
            return response.text
        except ValueError:
            return response.text

    def check_connection(self) -> WBResponse:
        """Проверка соединения с API"""
        return self._request('GET', '/v1/auth/test', use_cache=False)

    def invalidate_cache(self, endpoint: str, params: Optional[Dict] = None):
        """Инвалидация кэша для конкретного endpoint"""
        cache_key = self._generate_cache_key(endpoint, params)
        APICache.objects.filter(endpoint=cache_key).delete()
