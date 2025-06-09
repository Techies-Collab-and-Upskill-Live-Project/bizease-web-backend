from rest_framework import serializers
from .models import Inventory, Category

class CategorySerializer(serializers.ModelSerializer):
	class Meta:
		model = Category
		fields = [
			'name'
		]

class InventoryItemSerializer(serializers.ModelSerializer):
	class Meta:
		model = Inventory
		fields = [
			'id', 'product_name', 'description', 'stock_level', 'price', 'last_updated', 'low_stock_threshold'
		]

class InventoryListSerializer(serializers.Serializer):
	data = InventoryItemSerializer(many=True)