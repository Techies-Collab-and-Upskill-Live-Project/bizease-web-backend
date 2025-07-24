from django.db import models, transaction
from accounts.models import CustomUser
from django.db.models import Q
from inventory.models import Inventory
from django.utils import timezone

class Order(models.Model):
	product_owner_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
	client_name = models.CharField(max_length=150)
	client_email = models.CharField(max_length=150, blank=True)
	client_phone = models.CharField(max_length=150, blank=True)
	status = models.CharField(choices={"Pending": "Pending", "Delivered": "Delivered"}, default="Pending")
	order_date = models.DateField()
	delivery_date = models.DateField(null=True)
	total_price = models.DecimalField(max_digits=14, decimal_places=2, null=True)
	ordered_products_objects = []

	class Meta:
		ordering = ["-order_date"]
		constraints = [
			models.CheckConstraint(condition=Q(total_price__gt=0), name="total_price_gt_zero")
		]

	def __str__(self):
		return f"{self.client_name} - {self.id}"

	@transaction.atomic
	def save_order_to_db(self, products_err_dict, **kwargs):
		super().save(**kwargs) # Allows the model instance to get a db generated id that's required when saving ordered products that have a foreign key to it

		if len(self.ordered_products_objects) > 0: # new order
			self.total_price = 0
			
		non_unique_order_err = "Ordered products must be unique. Use the quantity field to specify multiple orders of same item."
		for product in self.ordered_products_objects:
			product.name = product.name.title()
			if products_err_dict.get(product.name) == None:
				products_err_dict[product.name] = []
			else:
				if non_unique_order_err not in products_err_dict[product.name]:
					products_err_dict[product.name].append(non_unique_order_err)
				continue

			if product.id != None:
				raise ValueError(f"Ordered product '{product.name}' has already been added to an order.", "custom")
			product.order_id = self
			errors = product.save()
			if errors:
				products_err_dict[product.name] += errors

		for k in products_err_dict.copy():
			if len(products_err_dict[k]) == 0:
				del products_err_dict[k]

		if products_err_dict:
			raise ValueError("Ordered item has one or more invalid attributes")

	@transaction.atomic
	def update_total_price(self, **kwargs):
		super().save(update_fields=['total_price'], **kwargs)

	def save(self, **kwargs):
		ordered_products = self.ordered_products_objects # An array of OrderedProducts instance whose data haven't been saved to the db

		actual_status_val = self.status
		self.status = self.status.title()

		if self.status not in ["Pending", "Delivered"]:
			return  {"order-errors": [f"Invalid Order status value '{actual_status_val}'"]}
		elif self.status == "Delivered" and not self.delivery_date:
			self.delivery_date = timezone.now().date()

		if not self.id: # new order
			self.total_price = None # Should be 'None' but no validation is carried out before hand so this is just making sure

		if (not self.id and ((type(ordered_products) != list) or not ordered_products)):
			raise ValueError('An Order must have at least one ordered product', "custom")

		products_err_dict = {}
		try:
			self.save_order_to_db(products_err_dict, **kwargs)
		except ValueError as val_err:
			# The error checked below might have been raised from the function in 
			# the try block intentionally to rollback current transaction
			if (str(val_err) != "Ordered item has one or more invalid attributes"): 
				# Error wasn't raised directly from the function in the try block (i.e. error from values violating db constraints)
				# So it needs to be handled properly outside this function
				raise ValueError(val_err)

		if products_err_dict:
			return products_err_dict

		self.ordered_products_objects = []
		self.update_total_price()


class OrderedProduct(models.Model):
	name = models.CharField(max_length=100)
	order_id = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="ordered_products")
	quantity = models.PositiveIntegerField()
	price = models.DecimalField(default=0, max_digits=14, decimal_places=2)
	cummulative_price = models.DecimalField(max_digits=14, decimal_places=2)

	class Meta:
		ordering = ["id"]
		constraints = [
			models.UniqueConstraint(fields=["order_id", "name"], name="unique_product_in_order"),
			models.CheckConstraint(condition=Q(price__gt=0), name="order_price_greater_than_zero"),
			models.CheckConstraint(condition=Q(cummulative_price__gt=0), name="cummulative_price_greater_than_zero")
		]

	def validate_data(self, inventory_product):
		errors = []
		if self.quantity <= 0 or type(self.quantity) != int:
			errors.append(f"Quantity must be an integer and must be equal to 1 at least")
		if self.quantity > inventory_product.stock_level:
			errors.append(f"Not enough products in stock to satisfy order for '{self.name}'")
		if self.price != inventory_product.price:
			errors.append(f"Price isn't the same as that of inventory item for '{self.name}'")
		return errors

	def create(self, inventory_product):
		inventory_product.stock_level -= self.quantity
		self.cummulative_price = self.price * self.quantity
		order_obj = self.order_id
		order_obj.total_price += self.cummulative_price

	def assert_only_quantity_is_updated(self, currentDbInstance):
		if (currentDbInstance.name != self.name):
			return ["Only 'quantity' field can be updated"]
		if (currentDbInstance.price != self.price):
			return ["Only 'quantity' field can be updated"]
		if (currentDbInstance.order_id != self.order_id):
			return ["Only 'quantity' field can be updated"]
		if (currentDbInstance.cummulative_price != self.cummulative_price):
			return ["Only 'quantity' field can be updated"]

	def update(self, inventory_product):
		currentDbInstance = OrderedProduct.objects.get(pk=self.id)
		errors = self.assert_only_quantity_is_updated(currentDbInstance)
		if errors:
			return errors

		prev_quantity = currentDbInstance.quantity
		if self.quantity > (inventory_product.stock_level + prev_quantity):
			return [f"Not enough products in stock to satisfy order for '{self.name}'"]

		inventory_product.stock_level = inventory_product.stock_level + prev_quantity - self.quantity
		self.cummulative_price = self.price * self.quantity
		order_obj = self.order_id
		order_obj.total_price = order_obj.total_price - (prev_quantity * self.price) + self.cummulative_price

	@transaction.atomic
	def save(self, *, new_order=True, **kwargs):
		try:
			if type(self.order_id) == int:
				self.order_id = Order.objects.get(pk=self.order_id)

			product_owner_id = self.order_id.product_owner_id
			inventory_product = Inventory.objects.filter(owner_id=product_owner_id).filter(product_name=self.name).get()
		except (Inventory.DoesNotExist, Inventory.MultipleObjectsReturned):
			return [f"'{self.name}' doesn't exist in the Inventory."]
		except (Order.DoesNotExist, Order.MultipleObjectsReturned):
			return [f"'{self.name}' Order doesn't exist."]
		errors = self.validate_data(inventory_product)
		if errors:
			return errors

		if self.id == None:
			self.create(inventory_product)
		else:
			update_errors = self.update(inventory_product)
			if update_errors:
				return update_errors

		inventory_product.save()
		super().save(**kwargs)
		if new_order == False: # this is an existing Order
			 # Updating the quantity of any of the ordered product of an order
			 # means the total_price will also increase
			self.order_id.update_total_price()

	@transaction.atomic
	def delete(self, **kwargs):
		item_in_stock = True
		try:
			order_obj = Order.objects.get(pk=self.order_id.id)
			inventory_product = Inventory.objects.filter(owner_id=order_obj.product_owner_id).filter(product_name=self.name).get()
		except (Order.DoesNotExist, Order.MultipleObjectsReturned):
			raise ValueError("Unexpected Error! ordered item to delete has no Order")
		except (Inventory.DoesNotExist, Inventory.MultipleObjectsReturned):
			item_in_stock = False

		if (order_obj.ordered_products.count() == 1):
			raise ValueError("Can't delete item! An Order must have at least one ordered product")

		order_obj.total_price -= (self.price * self.quantity)
		order_obj.save()
		if item_in_stock:
			inventory_product.stock_level += self.quantity
			inventory_product.save()

		super().delete(**kwargs)

	def __str__(self):
		return f"{self.name}({self.quantity})"