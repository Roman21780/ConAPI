from django.contrib import admin

from .client.client import WBClient
from .models import APICache
from django.utils.safestring import mark_safe
import json
from django.utils.timezone import now

@admin.register(APICache)
class APICacheAdmin(admin.ModelAdmin):
    list_display = ('endpoint_truncated', 'expires_at', 'is_expired')
    list_filter = ('expires_at',)
    search_fields = ('endpoint',)
    readonly_fields = ('endpoint', 'response_prettified', 'expires_at')
    exclude = ('response',)

    def endpoint_truncated(self, obj):
        return obj.endpoint[:50] + '...' if len(obj.endpoint) > 50 else obj.endpoint
    endpoint_truncated.short_description = 'Endpoint'

    def response_prettified(self, obj):
        try:
            response = json.loads(obj.response)
            return mark_safe(f'<pre>{json.dumps(response, indent=2, ensure_ascii=False)}</pre>')
        except json.JSONDecodeError:
            return mark_safe(f'<pre>{obj.response}</pre>')
    response_prettified.short_description = 'Response (formatted)'

    def is_expired(self, obj):
        return obj.expires_at < now()
    is_expired.boolean = True
    is_expired.short_description = 'Expired'

class WildberriesAdminArea(admin.AdminSite):
    site_header = 'Wildberries API Administration'
    site_title = 'Wildberries Admin'

wildberries_admin = WildberriesAdminArea(name='WildberriesAdmin')

@admin.action(description='Force refresh selected cache items')
def refresh_cache(modeladmin, request, queryset):
    client = WBClient(base_url="https://api.test", api_key="your_api_key")  # Инициализируем с параметрами
    for item in queryset:
        endpoint = item.endpoint.split(':')[0]
        if endpoint == 'get_products':  # Используем актуальные названия методов
            client.get_products(force_refresh=True)
        elif endpoint == 'get_product':
            product_id = item.endpoint.split(':')[1]
            client.update_product(product_id, force_refresh=True)  # Используем существующий метод

class WBAdminProxy(admin.ModelAdmin):
    actions = [refresh_cache]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(endpoint__startswith='get_')

wildberries_admin.register(APICache, WBAdminProxy)

# Основная админка
admin.site.site_header = 'OmniConnect Administration'
admin.site.index_title = 'Wildberries API Management'