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

	def create(self, validated_data):
		"""
		Create, save and return a new `Inventory` instance, given the validated data.
		"""
		validated_data["product_name"] = validated_data["product_name"].title() # Apply very basic normalization to the text
		new_product = CustomUser(**validated_data)
		new_product.save()
		return new_product

	def update(self, instance, validated_data):
		if validated_data.get("product_name"):
			validated_data["product_name"] = validated_data["product_name"].title() # Apply very basic normalization to the text
		return super().update(instance, validated_data)