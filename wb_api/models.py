from django.db import models

# Create your models here.


from django.db import models
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
import json

class APICache(models.Model):
    """
    Модель для хранения кэшированных ответов от API Wildberries
    """
    endpoint = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='API Endpoint'
    )
    response = models.JSONField(
        encoder=DjangoJSONEncoder,
        verbose_name='Response Data'
    )
    expires_at = models.DateTimeField(
        verbose_name='Expiration Time'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Creation Time'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Last Update'
    )

    class Meta:
        verbose_name = 'API Cache'
        verbose_name_plural = 'API Caches'
        indexes = [
            models.Index(fields=['endpoint']),
            models.Index(fields=['expires_at']),
        ]
        ordering = ['-expires_at']

    def __str__(self):
        return f"{self.endpoint} (expires: {self.expires_at})"

    @classmethod
    def get_cached_response(cls, endpoint, params=None):
        """
        Получение кэшированного ответа по endpoint и параметрам
        """
        cache_key = cls._generate_cache_key(endpoint, params)
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
        """
        Сохранение ответа в кэш
        """
        cache_key = cls._generate_cache_key(endpoint, params)
        cls.objects.update_or_create(
            endpoint=cache_key,
            defaults={
                'response': response,
                'expires_at': timezone.now() + timezone.timedelta(seconds=ttl)
            }
        )

    @classmethod
    def clear_expired(cls):
        """
        Очистка просроченного кэша
        """
        count, _ = cls.objects.filter(expires_at__lt=timezone.now()).delete()
        return count

    @classmethod
    def clear_all(cls):
        """
        Полная очистка кэша
        """
        count, _ = cls.objects.all().delete()
        return count

    @staticmethod
    def _generate_cache_key(endpoint, params=None):
        """
        Генерация ключа кэша на основе endpoint и параметров
        """
        if params:
            param_str = json.dumps(params, sort_keys=True)
            return f"{endpoint}:{param_str}"
        return endpoint


class WBAPIStats(models.Model):
    """
    Модель для хранения статистики запросов к API Wildberries
    """
    endpoint = models.CharField(max_length=100)
    request_count = models.PositiveIntegerField(default=0)
    success_count = models.PositiveIntegerField(default=0)
    last_response_time = models.FloatField(null=True, blank=True)
    last_request_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'API Statistics'
        verbose_name_plural = 'API Statistics'

    def __str__(self):
        return f"{self.endpoint} - {self.request_count} requests"

    @classmethod
    def record_request(cls, endpoint, success, response_time):
        """
        Запись статистики запроса
        """
        stats, _ = cls.objects.get_or_create(endpoint=endpoint)
        stats.request_count += 1
        if success:
            stats.success_count += 1
        stats.last_response_time = response_time
        stats.last_request_at = timezone.now()
        stats.save()


class WBProduct(models.Model):
    """
    Модель для хранения основных данных о товарах Wildberries
    (альтернативное кэширование для часто используемых товаров)
    """
    product_id = models.CharField(max_length=50, unique=True)
    name = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.PositiveIntegerField(default=0)
    total_stock = models.PositiveIntegerField(default=0)
    category = models.CharField(max_length=100, blank=True)
    brand = models.CharField(max_length=100, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    data = models.JSONField(default=dict)

    class Meta:
        verbose_name = 'WB Product'
        verbose_name_plural = 'WB Products'
        indexes = [
            models.Index(fields=['product_id']),
            models.Index(fields=['price']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return f"{self.product_id} - {self.name[:50]}"