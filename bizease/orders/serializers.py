from rest_framework import serializers
from .models import Order, OrderedProduct
from inventory.models import Inventory

class OrderedProductSerializer(serializers.ModelSerializer):
	class Meta:
		model = OrderedProduct
		fields = [
			'name', 'quantity', 'price'
		]

"""
{"client_name": "customer1", "client_email": "customer1@gmail.com", "status": "Pending", "ordered_products": [{"name": "NKJV Bible", "quantity": 3, "price": 5000}]}
"""

class OrderSerializer(serializers.ModelSerializer):
	class Meta:
		model = Order
		fields = [
			'id', 'client_name', 'client_email', 'client_phone', 'status', 'ordered_products', 'total_price'
		]
	total_price = serializers.IntegerField(required=False)
	ordered_products = OrderedProductSerializer(many=True)

	# todo: Wrap it all in a transaction
	def create(self, product_owner):
		ordered_products = self.validated_data["ordered_products"]
		if len(ordered_products) == 0:
			return {"detail": ["Order must contain at least one Ordered product"], "status": 400}

		del self.validated_data["ordered_products"] # ordered_products is not a column in Order table
		new_order = Order(**self.validated_data)
		new_order.product_owner_id = product_owner

		# Dictionary mapping available product name to an OrderedProducts instance with the same name
		ordered_products_dict = {}

		for product in ordered_products:
			product["name"] = product["name"].title() # normalization
			if not ordered_products_dict.get(product["name"]): # This product hasn't been previously encountered in the list
				ordered_products_dict[product["name"]] = OrderedProduct(
					name=product["name"], price=product["price"],
					quantity=product["quantity"]
				)
			else: # The same product was added to the order more than once. We don't want that, That's why we have a quantity field
				return {"detail": [f"Duplicate Ordered Product: {product['name']}. Use the quantity field to specify multiple items"], "status": 400}

		available_products = Inventory.objects.filter(owner_id=product_owner.id).filter(product_name__in=list(ordered_products_dict.keys()))
		if len(available_products) == 0:
			return {"detail": [f"Ordered items aren't in the inventory!"], "status": 400}
		errors = []
		for item in available_products:
			ordered_product = ordered_products_dict.get(item.product_name)
			if not ordered_product:
				errors.append(f"'{item.product_name}' Doesn't exist in the Inventory.")
			if ordered_product.quantity > item.stock_level:
				errors.append(f"Not enough products in stock to satisfy order for '{item.product_name}'")
			if ordered_product.price != item.price:
				errors.append(f"Price isn't the same as that of inventory item '{item.product_name}'")

			item.stock_level -= ordered_product.quantity 

		if errors:
			return {"detail": errors, "status": 400}

		new_order.save()
		for ordered_product in ordered_products_dict.values():
			ordered_product.cummulative_price=ordered_product.price * ordered_product.quantity
			ordered_product.order_id = new_order
			ordered_product.save()
			new_order.total_price += ordered_product.cummulative_price

		for item in available_products:
			item.save()

		new_order.save()
			
		return {"detail": "Order created successfully", "status": 200}

	def update(self, product_owner):
		"""
		Non editable fields (Order)
		product_owner_id
		total_price
		order_date

		Non editable fields (OrderedProducts)
		order_id
		cummulative_price

		Editable fields
		client_name
		client_email
		client_phone
		status

		name
		quantity
		price
		"""
		if self.instance.status != "Pending":
			return {"details": {"errors": ["Only pending orders can be edited"]}, "status": 400}

		self.instance.client_name = self.validated_data.get('client_name', self.instance.client_name)
		self.instance.client_email = self.validated_data.get('client_email', self.instance.client_email)
		self.instance.client_phone = self.validated_data.get('client_phone', self.instance.client_phone)

		self.instance.save()
		return {"details": {"msg": "Order Updated successfully"}, "status": 200}


	def save(self, product_owner):
		if self.instance:
			return self.update(product_owner)
		else:
			return self.create(product_owner)
class OrdersArraySerializers(serializers.Serializer):
	data = OrderSerializer(many=True)
