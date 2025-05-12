import datetime
from typing import Optional, Dict
from .base import WBClientBase, WBResponse
from .models.cache import cache_api_call
from .products import WBProductsClient
from .categories import WBCategoriesClient
from .orders import WBOrdersClient


class WildberriesClient(WBProductsClient, WBCategoriesClient, WBOrdersClient):
    def __init__(self, token: str):
        super().__init__(token)
        self.base_url = "https://suppliers-api.wildberries.ru"

    @cache_api_call(ttl=3600)
    @cache_api_call(ttl=3600)
    def check_creds(self, token: str) -> WBResponse:
        """Проверка валидности токена"""
        self.token = token
        try:
            # Получаем сырой ответ от API
            raw_response = self._request('GET', '/auth/test')

            # Если _request возвращает WBResponse (как в тестах)
            if isinstance(raw_response, WBResponse):
                return raw_response

            # Если _request возвращает requests.Response (реальный случай)
            return WBResponse(
                success=raw_response.ok,
                data={'valid': raw_response.ok},
                error=None if raw_response.ok else "Invalid token",
                status_code=raw_response.status_code
            )
        except Exception as e:
            return WBResponse(
                success=False,
                data=None,
                error=str(e),
                status_code=500
            )

    def _prepare_filter_params(self, filter: Optional[Dict] = None) -> Dict:
        """Подготовка параметров фильтрации"""
        params = {}
        if filter:
            if 'status' in filter:
                params['status'] = filter['status']
            if 'date_from' in filter:
                params['dateFrom'] = self._format_date(filter['date_from'])
            if 'date_to' in filter:
                params['dateTo'] = self._format_date(filter['date_to'])
            if 'limit' in filter:
                params['limit'] = filter['limit']
        return params

    def _format_date(self, date_value) -> str:
        """Форматирование даты"""
        if isinstance(date_value, datetime.datetime):
            return date_value.isoformat()
        return str(date_value)

    def _invalidate_cache(self, cache_key: str):
        """Инвалидация кэша"""
        from .models.cache import ClientAPICache
        ClientAPICache.objects.filter(endpoint__startswith=cache_key).delete()