from .base import WBClientBase, WBResponse
from .products import WBProductsClient
from .categories import WBCategoriesClient
from .orders import WBOrdersClient

class WildberriesClient(WBProductsClient, WBCategoriesClient, WBOrdersClient):
    def check_creds(self, token: str) -> WBResponse:
        """Проверка валидности токена"""
        self.token = token
        response = self._request('GET', '/v1/auth/test')
        return WBResponse(
            success=response.success,
            data={'valid': response.success},
            error=None if response.success else "Invalid token"
        )