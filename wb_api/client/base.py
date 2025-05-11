import requests
from django.conf import settings
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pydantic import BaseModel

from wb_api.exceptions import WBAuthError


@dataclass
class WBResponse:
    success: bool
    data: Optional[Dict[str, Any]]
    error: Optional[str]


class WBClientBase:
    def __init__(self, token: Optional[str] = None):
        self.base_url = getattr(settings, 'WB_API_URL', 'https://dev.wildberries.ru/api')
        self.token = token or getattr(settings, 'WB_API_TOKEN', None)
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        })

    def _request(
            self,
            method: str,
            endpoint: str,
            params: Optional[Dict] = None,
            data: Optional[Dict] = None
    ) -> WBResponse:
        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data
            )

            if response.status_code == 401:
                raise WBAuthError("Invalid API token")

            if response.status_code >= 400:
                return WBResponse(
                    success=False,
                    data=None,
                    error=f"API error: {response.text}"
                )

            return WBResponse(
                success=True,
                data=response.json(),
                error=None
            )

        except requests.exceptions.ConnectionError:
            return WBResponse(
                success=False,
                data=None,
                error="Connection error"
            )
        except Exception as e:
            return WBResponse(
                success=False,
                data=None,
                error=str(e)
            )