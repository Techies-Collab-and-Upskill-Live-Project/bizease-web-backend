from . import views
from django.urls import path

urlpatterns = [
	path('', views.OrdersView.as_view(), name="orders"),
	path('stats', views.OrderStatsView.as_view(), name="orders-stats"),
	path('<int:order_id>', views.SingleOrderView.as_view(), name="order"),
	path('<int:order_id>/ordered-products/<int:product_id>', views.OrderedProductView.as_view(), name="ordered-products"),
	path('<int:order_id>/ordered-products', views.OrderedProducts.as_view(), name="ordered-product"),
]