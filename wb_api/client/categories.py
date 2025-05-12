from .base import WBClientBase
from .models.cache import cache_api_call
from .models.schemas import CategorySchema, CategoryListSchema
from typing import Optional, Dict
from wb_api.models import WBResponse


class WBCategoriesClient(WBClientBase):
    @cache_api_call(ttl=86400)  # 24 часа кэширования для категорий
    def get_categories(self, filter: Optional[Dict] = None) -> WBResponse:
        """
        Получение списка категорий маркетплейса

        Args:
            filter: словарь с параметрами фильтрации:
                - parent_id: ID родительской категории
                - depth: глубина вложенности
        """
        params = {}
        if filter:
            if 'parent_id' in filter:
                params['parentId'] = filter['parent_id']
            if 'depth' in filter:
                params['depth'] = filter['depth']

        response = self._request('GET', '/v1/categories', params=params)
        if response.success:
            try:
                validated_data = CategoryListSchema.parse_obj(response.data)
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