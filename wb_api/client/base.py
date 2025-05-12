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
    data: Optional[Union[Dict[str, Any], list]]
    error: Optional[str]
    status_code: Optional[int] = None
    execution_time: Optional[float] = None

class WBClientBase:
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY = 1

    def __init__(self, token: Optional[str] = None):
        self.base_url = getattr(settings, 'WB_API_URL', 'https://dev.wildberries.ru/api')
        self.token = token or getattr(settings, 'WB_API_TOKEN', None)

        if not self.token:
            raise WBAuthError("API token is not configured")

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
            use_cache: bool = True,
            cache_ttl: int = 3600,
            force_refresh: bool = False
    ) -> WBResponse:
        """
        Улучшенный метод запроса с кэшированием и повторными попытками
        """
        cache_key = self._generate_cache_key(endpoint, params)
        start_time = time.time()

        # Пытаемся получить данные из кэша
        if use_cache and not force_refresh:
            cached_response = APICache.get_cached_response(endpoint, params)
            if cached_response is not None:
                return WBResponse(
                    success=True,
                    data=cached_response,
                    error=None,
                    status_code=200,
                    execution_time=time.time() - start_time
                )

        # Выполнение запроса с повторными попытками
        last_exception = None
        for attempt in range(self.MAX_RETRIES):
            try:
                url = f"{self.base_url}{endpoint}"
                if params and method == 'GET':
                    url = f"{url}?{urlencode(params)}"

                response = self.session.request(
                    method=method,
                    url=url,
                    params=params if method != 'GET' else None,
                    json=data,
                    timeout=self.DEFAULT_TIMEOUT
                )

                execution_time = time.time() - start_time

                # Логирование статистики
                WBAPIStats.record_request(
                    endpoint=endpoint,
                    success=response.status_code < 400,
                    response_time=execution_time
                )

                if response.status_code == 401:
                    raise WBAuthError("Invalid API token")

                if response.status_code >= 400:
                    error_msg = self._parse_error(response)
                    return WBResponse(
                        success=False,
                        data=None,
                        error=error_msg,
                        status_code=response.status_code,
                        execution_time=execution_time
                    )

                response_data = response.json()

                # Сохраняем в кэш успешные ответы
                if use_cache and response.status_code == 200:
                    APICache.set_cached_response(
                        endpoint=endpoint,
                        response=response_data,
                        params=params,
                        ttl=cache_ttl
                    )

                return WBResponse(
                    success=True,
                    data=response_data,
                    error=None,
                    status_code=response.status_code,
                    execution_time=execution_time
                )

            except requests.exceptions.ConnectionError as e:
                last_exception = e
                if attempt == self.MAX_RETRIES - 1:
                    return WBResponse(
                        success=False,
                        data=None,
                        error="Connection error after multiple retries",
                        status_code=503,
                        execution_time=time.time() - start_time
                    )
                time.sleep(self.RETRY_DELAY)

            except json.JSONDecodeError as e:
                return WBResponse(
                    success=False,
                    data=None,
                    error=f"Invalid JSON response: {str(e)}",
                    status_code=500,
                    execution_time=time.time() - start_time
                )

            except Exception as e:
                last_exception = e
                if attempt == self.MAX_RETRIES - 1:
                    return WBResponse(
                        success=False,
                        data=None,
                        error=str(e),
                        status_code=500,
                        execution_time=time.time() - start_time
                    )
                time.sleep(self.RETRY_DELAY)

        return WBResponse(
            success=False,
            data=None,
            error=str(last_exception) if last_exception else "Unknown error",
            status_code=500,
            execution_time=time.time() - start_time
        )

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