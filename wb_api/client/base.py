# wb_api/client/base.py
from dataclasses import dataclass
from typing import Any, Optional
import requests
from django.conf import settings

@dataclass
class WBResponse:
    success: bool
    data: Any
    error: Optional[str]
    status_code: int

class WBClientBase:
    BASE_URL = settings.WB_API_URL  # Используем URL из настроек

    def __init__(self, token: str = None):
        self.token = token or "test_key"
        self.BASE_URL = "https://api.test"  # Переопределяем для тестов
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        })

    def check_creds(self, token: str) -> WBResponse:
        """Проверка валидности токена"""
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        return self._request('GET', '/v1/auth/test')

    def get_products(self) -> WBResponse:
        """Получение списка товаров"""
        return self._request('GET', '/api/v1/supplier/stocks')

    def get_orders(self) -> WBResponse:
        """Получение списка заказов"""
        return self._request('GET', '/api/v1/supplier/orders')

    def _request(self, method: str, endpoint: str, **kwargs):
        url = f"{self.BASE_URL}{endpoint}"
        try:
            response = self.session.request(method, url, **kwargs)
            if response.status_code != 200:  # Добавьте эту проверку
                return WBResponse(
                    success=False,
                    data=None,
                    error=response.text,
                    status_code=response.status_code
                )
            return WBResponse(
                success=True,
                data=response.json() if response.content else None,
                error=None,
                status_code=response.status_code
            )
        except Exception as e:
            return WBResponse(
                success=False,
                data=None,
                error=f"Request failed: {str(e)}",  # Унифицированный формат ошибки
                status_code=500
            )