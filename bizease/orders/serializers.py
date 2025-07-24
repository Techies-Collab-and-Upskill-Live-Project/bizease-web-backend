from rest_framework import serializers
from .models import Order, OrderedProduct
from inventory.models import Inventory
from datetime import datetime
from django.db.utils import IntegrityError
from decimal import Decimal
from django.utils import timezone

def validate_decimal(value):
	if type(value) != int and type(value) != float and type(value) != Decimal:
		raise serializers.ValidationError("Value must be a float or an integer")

def validate_int(value):
	if type(value) != int:
		raise serializers.ValidationError("Value must be an integer")


class OrderedProductSerializer(serializers.ModelSerializer):
	class Meta:
		model = OrderedProduct
		fields = [
			'id', 'name', 'quantity', 'price', "cummulative_price"
		]

	cummulative_price = serializers.DecimalField(max_digits=14, decimal_places=2, required=False)
	quantity = serializers.IntegerField(min_value=1, validators=[validate_int])
	price = serializers.DecimalField(max_digits=14, decimal_places=2, validators=[validate_decimal])
	read_only_fields = ['id', 'name', 'price', 'cummulative_price']

	def update(self, instance, validated_data):
		errors = {}
		for key in validated_data:
			if key != "quantity": 
				# only the quantity field of a product can be updated once the product has been added to an order
				errors[key] = ["Unexpected field"]
		if errors:
			return {"errors": errors}

		if not validated_data.get("quantity"):
			return {"errors": {"quantity": "Field not present"}}

		instance.quantity = validated_data["quantity"]
		errors = instance.save(new_order=False)
		if errors:
			return {"errors": errors}
		else:
			return {"data": instance}

	def create(self, order):
		new_instance = OrderedProduct(**self.validated_data, order_id=order)
		errors = new_instance.save(new_order=False)
		if errors:
			return {"errors": errors}
		else:
			return {"data": new_instance}

	def save(self, order=None):
		if (order):
			return self.create(order)
		return super().save()

class OrderSerializer(serializers.ModelSerializer):
	class Meta:
		model = Order
		fields = [
			'id', 'client_name', 'client_email', 'client_phone', 'status', 'ordered_products', 'total_price', 'order_date', 'delivery_date'
		]
	total_price = serializers.IntegerField(required=False)
	order_date = serializers.DateField(required=True)
	ordered_products = OrderedProductSerializer(many=True)
	read_only_fields = ['id', 'delivery_date','total_price']

	def create(self, product_owner):
		ordered_products = self.validated_data["ordered_products"]
		if len(ordered_products) == 0:
			return {"detail": ["Order must contain at least one Ordered product"], "status": 400}

		del self.validated_data["ordered_products"] # ordered_products is not a column in Order table
		if self.validated_data.get("status") != "Delivered":
			if self.validated_data.get("delivery_date"):
				del self.validated_data["delivery_date"] # only 'Delivered' orders can have a delivery date

		new_order = Order(**self.validated_data)
		new_order.product_owner_id = product_owner
		new_order.ordered_products_objects = []

		for item in ordered_products:
			new_order.ordered_products_objects.append(OrderedProduct(**item))

		try:
			errors = new_order.save()
		except ValueError as err:
			if (err.args[1] == "custom"):
				return {"errors": {"ordered_products": err.args[0]}}
			else:
				return {"errors": "Fatal error"}
		except BaseException as err_1:
			return {"errors": "Fatal error"}
			
		if (errors):
			return {"errors": {"ordered_products": errors}}
		return {"data": new_order}


	def update(self, product_owner):
		if self.instance.status != "Pending":
			return {"detail": "Only pending orders can be edited", "status": 400}

		self.instance.client_name = self.validated_data.get('client_name', self.instance.client_name)
		self.instance.client_email = self.validated_data.get('client_email', self.instance.client_email)
		self.instance.client_phone = self.validated_data.get('client_phone', self.instance.client_phone)
		self.instance.order_date = self.validated_data.get('order_date', self.instance.order_date)
		self.instance.status = self.validated_data.get('status', self.instance.status)

		if self.instance.status == "Delivered":
			self.instance.delivery_date = timezone.now().date()

		try:
			errors = self.instance.save()
		except:
			return {"errors": "Fatal error"}
			
		if (errors):
			return {"errors": errors}
		return {"data": self.instance}


	def save(self, product_owner):
		if self.instance:
			return self.update(product_owner)
		else:
			return self.create(product_owner)
