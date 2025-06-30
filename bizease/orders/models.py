from django.db import models, transaction
from accounts.models import CustomUser
from django.db.models import Q
from inventory.models import Inventory

class Order(models.Model):
	product_owner_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
	client_name = models.CharField(max_length=150)
	client_email = models.CharField(max_length=150, blank=True)
	client_phone = models.CharField(max_length=150, blank=True)
	status = models.CharField(choices={"Pending": "Pending", "Delivered": "Delivered"}, default="Pending")
	order_date = models.DateTimeField(auto_now_add=True)
	delivery_date = models.DateTimeField(null=True)
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
		super().save(**kwargs)
		if len(self.ordered_products_objects) > 0:
			self.total_price = 0
		for product in self.ordered_products_objects:
			if product.id != None:
				raise ValueError(f"Ordered product '{product.name}' has already been added to another order.")
			product.order_id = self
			errors = product.save()
			if errors:
				products_err_dict[product.name] = errors
				raise ValueError("Ordered item has one or more invalid attributes")

	@transaction.atomic
	def update_total_price(self, **kwargs):
		super().save(update_fields=['total_price'], **kwargs)

	def save(self, **kwargs):
		ordered_products = self.ordered_products_objects # An array of OrderedProducts instance whose data haven't been saved to the db

		if (not self.id and ((type(ordered_products) != list) or not ordered_products)):
			raise ValueError('An Order must have at least one ordered product')

		products_err_dict = {}
		try:
			self.save_order_to_db(products_err_dict, **kwargs)
		except ValueError as val_err:
			if (str(val_err) != "Ordered item has one or more invalid attributes"):
				raise ValueError(val_err)

		if products_err_dict:
			return products_err_dict

		self.ordered_products_objects = []
		self.update_total_price()


class OrderedProduct(models.Model):
	name = models.CharField(max_length=100)
	order_id = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="ordered_products")
	quantity = models.PositiveIntegerField() # Add check constraint that make sure this field is gt_than_0
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
			raise ValueError("Only 'quantity' field can be updated")
		if (currentDbInstance.price != self.price):
			raise ValueError("Only 'quantity' field can be updated")
		if (currentDbInstance.order_id != self.order_id):
			raise ValueError("Only 'quantity' field can be updated")
		if (currentDbInstance.cummulative_price != self.cummulative_price):
			raise ValueError("Only 'quantity' field can be updated")

	def update(self, inventory_product):
		currentDbInstance = OrderedProduct.objects.get(pk=self.id)
		self.assert_only_quantity_is_updated(currentDbInstance)

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
			product_owner_id = self.order_id.product_owner_id
			inventory_product = Inventory.objects.filter(owner_id=product_owner_id).filter(product_name=self.name.title()).get()
		except (Inventory.DoesNotExist, Inventory.MultipleObjectsReturned, Order.DoesNotExist, Order.MultipleObjectsReturned):
			return [f"'{self.name}' doesn't exist in the Inventory."]
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
		if new_order == False:
			self.order_id.update_total_price()

	def __str__(self):
		return f"{self.name}({self.quantity})"