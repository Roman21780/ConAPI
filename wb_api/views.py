from django.views.generic import TemplateView

from wb_api.client.client import WBClient
from wb_api.client.orders import WBOrdersClient
from wb_api.client.products import WBProductsClient
from wb_api.client.categories import WBCategoriesClient
from django.conf import settings


class DashboardView(TemplateView):
    template_name = 'wb_api/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = WBClient  # Используйте токен из настроек
        context["products"] = client.get_products
        return context


class OrdersView(TemplateView):
    template_name = 'wb_api/orders.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = WBOrdersClient(token=settings.WB_API_TOKEN)  # Используйте токен из настроек
        context["orders"] = client.get_orders()
        return context


class CategoriesView(TemplateView):
    template_name = 'wb_api/categories.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = WBCategoriesClient(token=settings.WB_API_TOKEN)  # Передаем токен
        context["categories"] = client.get_categories()
        return context





