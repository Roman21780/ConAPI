# wb_api/client/orders.py
from typing import Dict, Any, Optional
from .base import WBClientBase, WBResponse
from .models.cache import cache_api_call


class WBOrdersClient(WBClientBase):
    @cache_api_call(ttl=3600)
    def get_orders(self, params: Optional[Dict[str, Any]] = None) -> WBResponse:
        response = self._request("GET", "/api/v1/orders", params=params)

        if response.success and isinstance(response.data, dict):
            # Нормализуем данные для единообразия
            orders = response.data.get('orders', [])
            return WBResponse(
                success=True,
                data={'orders': orders},
                error=None,
                status_code=200
            )
        return response