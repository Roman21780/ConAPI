from celery import shared_task
from django.utils import timezone
from wb_api.models import APICache
import logging

logger = logging.getLogger(__name__)

@shared_task
def clear_wb_cache_task(force=False):
    """Фоновая задача для очистки кэша"""
    try:
        if force:
            count, _ = APICache.objects.all().delete()
            logger.info(f"Принудительно очищен весь кэш. Удалено: {count}")
        else:
            count, _ = APICache.objects.filter(expires_at__lt=timezone.now()).delete()
            logger.info(f"Очищен просроченный кэш. Удалено: {count}")
        return count
    except Exception as e:
        logger.error(f"Ошибка очистки кэша: {str(e)}")
        raise