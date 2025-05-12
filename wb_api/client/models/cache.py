from django.db import models
from django.utils import timezone
import json
from datetime import timedelta
from functools import wraps

from wb_api.client import WBResponse


class ClientAPICache(models.Model):
    endpoint = models.CharField(max_length=255, unique=True)
    response = models.JSONField()
    expires_at = models.DateTimeField()

    @classmethod
    def set_cached_response(cls, endpoint, response, params=None, ttl=300):
        from django.utils import timezone
        from datetime import timedelta
        import json

        cache_key = f"{endpoint}:{json.dumps(params, sort_keys=True) if params else ''}"

        serialized_data = {
            'success': response.success,
            'data': response.data,
            'error': response.error,
            'status_code': response.status_code
        }

        cls.objects.update_or_create(
            endpoint=cache_key,
            defaults={
                'response': serialized_data,
                'expires_at': timezone.now() + timedelta(seconds=ttl)
            }
        )

    @classmethod
    def get_cached_response(cls, endpoint, params=None):
        import json
        from django.utils import timezone

        cache_key = f"{endpoint}:{json.dumps(params, sort_keys=True) if params else ''}"
        try:
            cached = cls.objects.get(endpoint=cache_key)
            if cached.expires_at > timezone.now():
                return cached.response
            cached.delete()
        except cls.DoesNotExist:
            return None


def cache_api_call(ttl=300):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            cache_key = f"{func.__name__}:{args}:{kwargs}"

            # Проверка кэша
            cached = ClientAPICache.get_cached_response(cache_key)
            if cached:
                return WBResponse(**cached)

            # Вызов оригинальной функции
            result = func(self, *args, **kwargs)

            # Сохранение в кэш
            if isinstance(result, WBResponse):
                ClientAPICache.set_cached_response(
                    endpoint=cache_key,
                    response=result,
                    ttl=ttl
                )

            return result

        return wrapper

    return decorator