import datetime
from typing import Optional, Dict

from celery.contrib.pytest import celery_app

from .base import WBClientBase, WBResponse
from .models.cache import cache_api_call
from .products import WBProductsClient
from .categories import WBCategoriesClient
from .orders import WBOrdersClient

__all__ = ('celery_app',)

class WildberriesClient(WBProductsClient, WBCategoriesClient, WBOrdersClient):
    @cache_api_call(ttl=3600)  # 1 час кэширования для проверки токена
    def check_creds(self, token: str) -> WBResponse:
        """Проверка валидности токена"""
        self.token = token
        response = self._request('GET', '/v1/auth/test')
        return WBResponse(
            success=response.success,
            data={'valid': response.success},
            error=None if response.success else "Invalid token"
        )

    def _prepare_filter_params(self, filter: Optional[Dict] = None) -> Dict:
        """Вспомогательный метод для подготовки параметров фильтрации"""
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
        """Форматирование даты в строку"""
        if isinstance(date_value, datetime):
            return date_value.isoformat()
        return date_value

    def _validate_response(self, response: WBResponse, schema) -> WBResponse:
        """Валидация ответа API с помощью Pydantic схемы"""
        if response.success:
            try:
                validated_data = schema.parse_obj(response.data)
                return WBResponse(
                    success=True,
                    data=validated_data.dict(),
                    error=None
                )
            except Exception as e:
                return WBResponse(
                    success=False,
                    data=None,
                    error=f"Validation error: {str(e)}"
                )
        return response

    def _invalidate_cache(self, cache_key: str):
        """Инвалидация кэша по ключу"""
        from .models.cache import ClientAPICache
        ClientAPICache.objects.filter(endpoint__startswith=cache_key).delete()