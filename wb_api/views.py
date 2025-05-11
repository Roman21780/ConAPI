from django.shortcuts import render

# Create your views here.

from django.views import View
from .client import WildberriesClient
import json


class DashboardView(View):
    template_name = 'wb_api/dashboard.html'

    def get(self, request):
        client = WildberriesClient()
        response = client.get_prds(filter={"limit": 10})

        products = response.data.get('items', []) if response.success else []

        context = {
            'products': products,
            'products_json': json.dumps(products, ensure_ascii=False)
        }
        return render(request, self.template_name, context)


class OrdersView(View):
    template_name = 'wb_api/orders.html'

    def get(self, request):
        client = WildberriesClient()
        response = client.get_orders(filter={"limit": 10})

        orders = response.data.get('items', []) if response.success else []
        return render(request, self.template_name, {'orders': orders})


class CategoriesView(View):
    template_name = 'wb_api/categories.html'

    def get(self, request):
        client = WildberriesClient()
        response = client.get_categories()

        categories = response.data.get('items', []) if response.success else []
        return render(request, self.template_name, {'categories': categories})
