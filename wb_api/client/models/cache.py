from django.db import models
from django.utils import timezone
import json
from datetime import timedelta


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


def cache_api_call(ttl=3600):
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            endpoint = func.__name__
            params = kwargs.get('filter', {})

            # Пытаемся получить из кэша
            cached = ClientAPICache.get_cached_response(endpoint, params)
            if cached is not None:
                return cached

            # Выполняем запрос
            response = func(self, *args, **kwargs)

            # Кэшируем успешные ответы
            if response.success:
                ClientAPICache.set_cached_response(
                    endpoint=endpoint,
                    response=response,
                    params=params,
                    ttl=ttl
                )

            return response

        return wrapper

    return decorator