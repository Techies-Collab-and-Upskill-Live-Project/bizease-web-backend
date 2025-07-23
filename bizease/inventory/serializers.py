from rest_framework import serializers
from .models import Inventory

class InventoryItemSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(default=0, max_digits=14, decimal_places=2, min_value=0)

    class Meta:
        model = Inventory
        fields = [
            'id', 'product_name', 'description', 'stock_level', 'price', 'last_updated', 'low_stock_threshold', 'category', 'date_added'
        ]
        read_only_fields = ["id", "last_updated"]

    def validate(self, data):
        """ Checks for unwanted fields"""
        expected_validated_data = {} # will be used to hold only values from Meta.fields
        good = True

        for field in self.Meta.fields:
            field_value = self.initial_data.get(field)
            if field_value and (field not in self.Meta.read_only_fields):
                expected_validated_data[field] = field_value
                del self.initial_data[field]

        for key in self.initial_data:
            self.initial_data[key] = ["Unexpected field"]
            good = False

        if not good:
            return {"field_errors": self.initial_data}
        return data
    
    
    def save(self, owner):
        if self.validated_data.get('product_name'):
            self.validated_data["product_name"] = self.validated_data["product_name"].title() # Apply very basic normalization to the text

        if self.validated_data.get('category'):
            self.validated_data['category'] = self.validated_data['category'].title() # Apply very basic normalization to the text

        self.validated_data['owner'] = owner

        if self.validated_data.get("field_errors"):
            del self.validated_data["field_errors"]

        return super().save()