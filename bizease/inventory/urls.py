from . import views
from django.urls import path

urlpatterns = [
	path('', views.InventoryView.as_view()),
	path('stats', views.InventoryStatsView.as_view()),
	path('<int:item_id>', views.InventoryItemView.as_view()),
]