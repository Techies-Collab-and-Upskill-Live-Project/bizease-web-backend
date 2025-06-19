from . import views
from django.urls import path

urlpatterns = [
	path('', views.OrdersView.as_view()),
	path('stats', views.OrderStatsView.as_view()),
	path('<int:item_id>', views.SingleOrderView.as_view()),
]