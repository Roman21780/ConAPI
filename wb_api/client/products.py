from .base import WBClientBase, WBResponse
from .models.schemas import ProductSchema, ProductListSchema
from datetime import datetime
from typing import Optional, Dict, Any


class WBProductsClient(WBClientBase):
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

        response = self._request('GET', '/v1/products', params=params)
        if response.success:
            try:
                validated_data = ProductListSchema.parse_obj(response.data)
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

    def get_prd(self, prd_id: str) -> WBResponse:
        """Получение полной информации о товаре"""
        response = self._request('GET', f'/v1/products/{prd_id}')
        if response.success:
            try:
                validated_data = ProductSchema.parse_obj(response.data)
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

    def set_prd(self, prd_id: str, data: Dict[str, Any]) -> WBResponse:
        """Изменение атрибутов товара"""
        try:
            # Валидируем входные данные
            product_data = ProductSchema(**data).dict(exclude_unset=True)
            return self._request('PATCH', f'/v1/products/{prd_id}', data=product_data)
        except Exception as e:
            return WBResponse(
                success=False,
                data=None,
                error=f"Validation error: {str(e)}"
            )

    def get_comission(self, prd_id: str) -> WBResponse:
        """Получение информации о комиссии для товара"""
        return self._request('GET', f'/v1/products/{prd_id}/commission')