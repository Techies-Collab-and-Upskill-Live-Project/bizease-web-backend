from . import views
from django.urls import path

urlpatterns = [
	path('', views.InventoryView.as_view()),
	path('<int:itemId>', views.InventoryItemView.as_view()),
]