from .base import WBClientBase, WBResponse
from .models.schemas import OrderSchema, OrderListSchema
from datetime import datetime
from typing import Optional, Dict


class WBOrdersClient(WBClientBase):
    def get_orders(self, filter: Optional[Dict] = None) -> WBResponse:
        """
        Получение списка заказов

        Args:
            filter: словарь с параметрами фильтрации:
                - date_from: дата начала периода
                - date_to: дата окончания периода
                - status: статус заказа
                - limit: ограничение количества
        """
        params = {}
        if filter:
            if 'date_from' in filter:
                if isinstance(filter['date_from'], datetime):
                    params['dateFrom'] = filter['date_from'].isoformat()
                else:
                    params['dateFrom'] = filter['date_from']
            if 'status' in filter:
                params['status'] = filter['status']
            if 'limit' in filter:
                params['limit'] = filter['limit']

        response = self._request('GET', '/v1/orders', params=params)
        if response.success:
            try:
                validated_data = OrderListSchema.parse_obj(response.data)
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