from django.views.generic import TemplateView
from wb_api.client.orders import WBOrdersClient
from wb_api.client.products import WBProductsClient
from wb_api.client.categories import WBCategoriesClient


class DashboardView(TemplateView):
    template_name = 'wb_api/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = WBProductsClient()
        response = client.get_prds(filter={"limit": 10})  # Изменили на get_prds
        context['products'] = response.data if response.success else []
        return context


class OrdersView(TemplateView):
    template_name = 'wb_api/orders.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = WBOrdersClient()
        response = client.get_orders()  # Этот метод существует
        context['orders'] = response.data if response.success else []
        return context


class CategoriesView(TemplateView):
    template_name = 'wb_api/categories.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = WBCategoriesClient()
        response = client.get_categories()  # Этот метод существует
        context['categories'] = response.data if response.success else []
        return context