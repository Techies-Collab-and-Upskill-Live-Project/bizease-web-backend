from django.db import models
from inventory.models import Inventory

class Order(models.Model):
	client_name = models.CharField(max_length=150)
	client_email = models.CharField(max_length=150, blank=True)
	client_phone = models.CharField(max_length=150, blank=True)
	status = models.CharField(choices={"Pending": "Pending", "Delivered": "Delivered"}, null=True)
	order_date = models.DateField(auto_now_add=True)

	class Meta:
		ordering = ["-order_date"]

	def __str__(self):
		return f"{self.client_name} - {self.order_id}"


class OrderedProduct(models.Model):
	product_ordered = models.CharField(max_length=100)
	order_id = models.ForeignKey(Order, on_delete=models.CASCADE)
	quantity = models.IntegerField()
	cummulative_price = models.IntegerField()

	class Meta:
		constraints = [models.UniqueConstraint(fields=["order_id", "product_ordered"], name="unique_product_in_order")]
		# add check constraint such that quantity is never less than 1 and cumm_price only ever approaches 0.

	# check if the product_ordered field value exists in orders and check if it's still in stock before saving