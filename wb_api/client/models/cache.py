from django.db import models
from django.utils import timezone


class ClientAPICache(models.Model):
    endpoint = models.CharField(max_length=255, unique=True)
    response = models.JSONField()
    expires_at = models.DateTimeField()

    @classmethod
    def get_cached_response(cls, endpoint, params=None):
        cache_key = f"{endpoint}:{str(params)}"
        try:
            cache = cls.objects.get(endpoint=cache_key)
            if cache.expires_at > timezone.now():
                return cache.response
            cache.delete()
        except cls.DoesNotExist:
            pass
        return None

    @classmethod
    def set_cached_response(cls, endpoint, response, params=None, ttl=3600):
        cache_key = f"{endpoint}:{str(params)}"
        cls.objects.update_or_create(
            endpoint=cache_key,
            defaults={
                'response': response,
                'expires_at': timezone.now() + timezone.timedelta(seconds=ttl)
            }
        )


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