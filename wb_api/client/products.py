from .base import WBClientBase, WBResponse
from .models.cache import cache_api_call
from .models.schemas import ProductSchema, ProductListSchema
from datetime import datetime
from typing import Optional, Dict, Any


class WBProductsClient(WBClientBase):
    @cache_api_call(ttl=1800)  # 30 минут кэширования для списка товаров
    def get_prds(self, filter: Optional[Dict] = None) -> WBResponse:
        """
        Получение списка товаров продавца с возможностью фильтрации

        Args:
            filter: словарь с параметрами фильтрации:
                - status: активный/неактивный
                - date_from: дата начала периода
                - date_to: дата окончания периода
                - limit: ограничение количества
        """
        params = {}
        if filter:
            if 'status' in filter:
                params['status'] = filter['status']
            if 'date_from' in filter:
                if isinstance(filter['date_from'], datetime):
                    params['dateFrom'] = filter['date_from'].isoformat()
                else:
                    params['dateFrom'] = filter['date_from']
            if 'limit' in filter:
                params['limit'] = filter['limit']

        response = self._request('GET', '/swagger/products', params=params)

        try:
            if isinstance(response, WBResponse):
                return response

            validated_data = ProductListSchema.parse_obj(response.json())
            return WBResponse(
                success=True,
                data=validated_data.dict(by_alias=True),
                error=None,
                status_code=response.status_code  # Добавляем status_code
            )
        except Exception as e:
            return WBResponse(
                success=False,
                data=None,
                error=f"Validation error: {str(e)}",
                status_code=500  # Добавляем status_code
            )

    @cache_api_call(ttl=3600)
    def get_prd(self, prd_id: str) -> WBResponse:
        """Получение информации о товаре"""
        response = self._request('GET', f'/swagger/products/{prd_id}')
        if isinstance(response, WBResponse):
            return response

        try:
            validated = ProductSchema.parse_obj(response.json())
            return WBResponse(
                success=True,
                data=validated.dict(),
                error=None,
                status_code=response.status_code
            )
        except Exception as e:
            return WBResponse(
                success=False,
                data=None,
                error=str(e),
                status_code=500
            )

    def set_prd(self, prd_id: str, data: Dict) -> WBResponse:
        """Обновление товара"""
        try:
            # Преобразуем входные данные
            update_data = {k: v for k, v in data.items() if v is not None}
            response = self._request('PATCH', f'/swagger/products/{prd_id}', json=update_data)

            self._invalidate_cache(f'get_prd:{prd_id}')
            return WBResponse(
                success=response.ok,
                data=response.json() if response.ok else None,
                error=None if response.ok else response.text,
                status_code=response.status_code
            )
        except Exception as e:
            return WBResponse(
                success=False,
                data=None,
                error=str(e),
                status_code=500
            )

    @cache_api_call(ttl=86400)  # 24 часа кэширования для комиссий
    def get_comission(self, prd_id: str) -> WBResponse:
        """Получение информации о комиссии для товара"""
        return self._request('GET', f'/swagger/products/{prd_id}/commission')