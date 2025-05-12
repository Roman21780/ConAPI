from typing import Optional, Dict, Any
import requests
from wb_api.models import WBResponse

class WBClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })

    def check_creds(self, token: str) -> WBResponse:
        """Проверка валидности токена"""
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        try:
            response = self.session.get(f"{self.base_url}/v1/auth/test")
            return WBResponse(
                success=response.status_code == 200,
                data=response.json() if response.status_code == 200 else None,
                error=None if response.status_code == 200 else response.text
            )
        except Exception as e:
            return WBResponse(success=False, data=None, error=str(e))

    def _request(self, method: str, endpoint: str, **kwargs) -> WBResponse:
        """Базовый метод для выполнения запросов"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()

            return WBResponse(
                success=True,
                data=response.json() if response.content else None,
                error=None
            )

        except requests.exceptions.HTTPError as http_err:
            return WBResponse(
                success=False,
                data=None,
                error=f"HTTP error: {http_err} - {response.text if 'response' in locals() else ''}"
            )
        except requests.exceptions.RequestException as req_err:
            return WBResponse(
                success=False,
                data=None,
                error=f"Request failed: {req_err}"
            )
        except Exception as e:
            return WBResponse(
                success=False,
                data=None,
                error=f"Unexpected error: {e}"
            )

    def get_products(self, force_refresh: bool = False) -> WBResponse:
        """Получение списка товаров с опцией принудительного обновления"""
        if force_refresh:
            # Логика принудительного обновления кэша
            self.session.headers.update({'Cache-Control': 'no-cache'})
        return self._request('GET', '/v1/products')

    def update_product(self, product_id: str, data: Dict[str, Any], force_refresh: bool = False) -> WBResponse:
        """Обновление товара с опцией принудительного обновления"""
        if force_refresh:
            self.session.headers.update({'Cache-Control': 'no-cache'})
        return self._request('PUT', f'/v1/products/{product_id}', json=data)

    def get_orders(self) -> WBResponse:
        """Получение списка заказов"""
        return self._request('GET', '/v1/orders')

    def get_categories(self) -> WBResponse:
        """Получение списка категорий"""
        return self._request('GET', '/v1/categories')