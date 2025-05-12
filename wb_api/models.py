from django.db import models
from datetime import timedelta

# Create your models here.


from django.db import models
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
import json

class APICacheManager(models.Manager):
    def clear_expired(self):
        from django.utils import timezone
        return self.filter(expires_at__lt=timezone.now()).delete()

class APICache(models.Model):
    objects = APICacheManager()
    endpoint = models.CharField(max_length=255, unique=True)
    response = models.JSONField()
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'api_cache'
        indexes = [
            models.Index(fields=['endpoint']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"Cache for {self.endpoint}"

    @classmethod
    def set_cached_response(cls, endpoint, response, params=None, ttl=300):
        # response должен быть WBResponse
        cache_key = f"{endpoint}:{json.dumps(params, sort_keys=True) if params else ''}"

        cls.objects.update_or_create(
            endpoint=cache_key,
            defaults={
                'response': {
                    'success': response.success,
                    'data': response.data,
                    'error': response.error,
                    'status_code': response.status_code
                },
                'expires_at': timezone.now() + timedelta(seconds=ttl)
            }
        )

    @classmethod
    def get_cached_response(cls, endpoint, params=None):
        cache_key = f"{endpoint}:{json.dumps(params, sort_keys=True) if params else ''}"
        try:
            cached = cls.objects.get(endpoint=cache_key)
            if cached.expires_at > timezone.now():
                return cached.response
            cached.delete()
        except cls.DoesNotExist:
            return None

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