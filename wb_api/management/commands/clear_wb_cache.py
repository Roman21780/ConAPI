from django.core.management.base import BaseCommand
from wb_api.models import APICache
from django.utils import timezone

class Command(BaseCommand):
    help = 'Очищает просроченный кэш Wildberries API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Очистить ВЕСЬ кэш (включая не просроченный)'
        )

    def handle(self, *args, **options):
        if options['all']:
            count, _ = APICache.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f'Очищен весь кэш. Удалено записей: {count}'))
        else:
            count, _ = APICache.objects.filter(expires_at__lt=timezone.now()).delete()
            self.stdout.write(self.style.SUCCESS(f'Очищен просроченный кэш. Удалено записей: {count}'))