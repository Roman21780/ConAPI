# wb_api/views.py
from django.views.generic import TemplateView
from wb_api.client.orders import WBOrdersClient
from wb_api.client.products import WBProductsClient
from wb_api.client.categories import WBCategoriesClient


class DashboardView(TemplateView):
    template_name = 'wb_api/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = WBProductsClient()
        response = client.get_prds()

        if response.success:
            context["products"] = response.data.get('products', [])
        else:
            context["error"] = response.error
            context["products"] = []

        return context


class OrdersView(TemplateView):
    template_name = 'wb_api/orders.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = WBOrdersClient()
        response = client.get_orders()

        if response.success:
            context["orders"] = response.data.get('orders', [])
        else:
            context["error"] = response.error
            context["orders"] = []

        return context


class CategoriesView(TemplateView):
    template_name = 'wb_api/categories.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = WBCategoriesClient()
        response = client.get_categories()

        if response.success:
            context["categories"] = response.data.get('categories', [])
        else:
            context["error"] = response.error
            context["categories"] = []

        return context