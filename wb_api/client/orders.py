from .base import WBClientBase
from .models.cache import cache_api_call
from .models.schemas import OrderSchema, OrderListSchema
from datetime import datetime
from typing import Optional, Dict
from wb_api.models import WBResponse


class WBOrdersClient(WBClientBase):
    @cache_api_call(ttl=900)  # 15 минут кэширования для заказов
    def get_orders(self):
        response = self.session.get("/orders")  # Предположим, что это запрос к API
        return WBResponse(
            success=response.status_code == 200,
            data=response.json() if response.status_code == 200 else None,
            error=response.text if response.status_code != 200 else None
        )
