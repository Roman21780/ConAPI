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
        self.token = token or settings.WB_API_TOKEN
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        })

    def _request(self, method: str, endpoint: str, **kwargs):
        url = f"{self.BASE_URL}{endpoint}"
        try:
            response = self.session.request(method, url, **kwargs)
            return WBResponse(
                success=response.status_code == 200,
                data=response.json() if response.status_code == 200 else None,
                error=None if response.status_code == 200 else response.text,
                status_code=response.status_code
            )
        except Exception as e:
            return WBResponse(
                success=False,
                data=None,
                error=str(e),
                status_code=500
            )