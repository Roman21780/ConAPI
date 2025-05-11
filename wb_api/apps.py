from datetime import timezone
from django.apps import AppConfig

class WbApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'wb_api'

    def ready(self):
        # Инициализация кэша
        from .client.models.cache import APICache
        APICache.objects.filter(expires_at__lt=timezone.now()).delete()
