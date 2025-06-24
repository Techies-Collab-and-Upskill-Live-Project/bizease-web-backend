from django.db import models
from accounts.models import CustomUser

class Order(models.Model):
	product_owner_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
	client_name = models.CharField(max_length=150)
	client_email = models.CharField(max_length=150, blank=True)
	client_phone = models.CharField(max_length=150, blank=True)
	status = models.CharField(choices={"Pending": "Pending", "Delivered": "Delivered"}, null=True)
	order_date = models.DateTimeField(auto_now_add=True)
	delivery_date = models.DateTimeField(null=True)
	total_price = models.IntegerField(default=0)

	class Meta:
		ordering = ["-order_date"]

	def __str__(self):
		return f"{self.client_name} - {self.id}"


class OrderedProduct(models.Model):
	name = models.CharField(max_length=100)
	order_id = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="ordered_products")
	quantity = models.IntegerField()
	price = models.IntegerField(default=0)
	cummulative_price = models.IntegerField() # should be a generated column since it's quantity x price?

	class Meta:
		constraints = [models.UniqueConstraint(fields=["order_id", "name"], name="unique_product_in_order")]
		# add check constraint such that quantity is never less than 1 and cumm_price only ever approaches 0.

	def __str__(self):
		return f"{self.name}({self.quantity})"