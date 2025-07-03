from . import views
from django.urls import path

urlpatterns = [
	path('', views.InventoryView.as_view(), name="inventory"),
	path('stats', views.InventoryStatsView.as_view(), name="inventory-stats"),
	path('<int:item_id>', views.InventoryItemView.as_view(), name="inventory-item"),
]