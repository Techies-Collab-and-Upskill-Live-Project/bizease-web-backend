from rest_framework import serializers
from .models import Inventory

class InventoryItemSerializer(serializers.ModelSerializer):
	class Meta:
		model = Inventory
		fields = [
			'id', 'product_name', 'description', 'stock_level', 'price', 'last_updated', 'low_stock_threshold', 'category'
		]
		read_only_fields = ["id"]

	def save(self, owner):
		if self.validated_data.get('product_name'):
			self.validated_data["product_name"] = self.validated_data["product_name"].title() # Apply very basic normalization to the text

		if self.validated_data.get('category'):
			self.validated_data['category'] = self.validated_data['category'].title() # Apply very basic normalization to the text
		self.validated_data['owner'] = owner

		return super().save()