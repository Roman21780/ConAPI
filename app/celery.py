import os
from celery import Celery
from django.conf import settings

# Установите переменную окружения для Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')

# Создаем экземпляр Celery
app = Celery('your_project')

# Загружаем конфигурацию из settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматическое обнаружение задач в приложениях
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# Настройка расписания
app.conf.beat_schedule = {
    'clear-wb-cache-nightly': {
        'task': 'wb_api.tasks.clear_wb_cache_task',
        'schedule': 86400,  # Каждые 24 часа (в секундах)
        'args': (False,),
    },
}