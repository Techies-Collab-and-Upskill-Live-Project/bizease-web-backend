from . import views
from django.urls import path

urlpatterns = [
	path('', views.OrdersView.as_view(), name="orders"),
	path('stats', views.OrderStatsView.as_view(), name="orders-stats"),
	path('<int:order_id>', views.SingleOrderView.as_view(), name="order"),
	path('<int:order_id>/ordered-products/<int:product_id>', views.SingleOrderedProductView.as_view(), name="ordered-product"),
	path('<int:order_id>/ordered-products', views.OrderedProductsView.as_view(), name="ordered-products"),
]