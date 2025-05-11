from django.contrib import admin

# Register your models here.


from django.contrib import admin
from .models import APICache
from .client import WildberriesClient
from django.utils.safestring import mark_safe
import json

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
        response = json.loads(obj.response)
        return mark_safe(f'<pre>{json.dumps(response, indent=2, ensure_ascii=False)}</pre>')
    response_prettified.short_description = 'Response (formatted)'

    def is_expired(self, obj):
        from django.utils.timezone import now
        return obj.expires_at < now()
    is_expired.boolean = True
    is_expired.short_description = 'Expired'

class WildberriesAdminArea(admin.AdminSite):
    site_header = 'Wildberries API Administration'
    site_title = 'Wildberries Admin'

wildberries_admin = WildberriesAdminArea(name='WildberriesAdmin')

@admin.action(description='Force refresh selected cache items')
def refresh_cache(modeladmin, request, queryset):
    client = WildberriesClient()
    for item in queryset:
        endpoint = item.endpoint.split(':')[0]
        if endpoint == 'get_prds':
            client.get_prds(force_refresh=True)
        elif endpoint == 'get_prd':
            product_id = item.endpoint.split(':')[1]
            client.get_prd(product_id, force_refresh=True)

class WBAdminProxy(admin.ModelAdmin):
    actions = [refresh_cache]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(endpoint__startswith='get_')

wildberries_admin.register(APICache, WBAdminProxy)

# Регистрация в основной админке
admin.site.site_header = 'OmniConnect Administration'
admin.site.index_title = 'Wildberries API Management'