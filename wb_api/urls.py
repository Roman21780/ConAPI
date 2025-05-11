from django.urls import path
from .views import DashboardView, OrdersView, CategoriesView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='wb_dashboard'),
    path('orders/', OrdersView.as_view(), name='wb_orders'),
    path('categories/', CategoriesView.as_view(), name='wb_categories'),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)