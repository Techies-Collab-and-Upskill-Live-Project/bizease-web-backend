from . import views
from django.urls import path

urlpatterns = [
	path('', views.OrdersView.as_view()),
	path('<int:itemId>', views.SingleOrderView.as_view()),
]