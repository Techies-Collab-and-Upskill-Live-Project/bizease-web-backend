from django.db import models
from accounts.models import CustomUser
from django.db.models import Q

class Inventory(models.Model):
	owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
	product_name = models.CharField(max_length=100)
	description = models.CharField(max_length=300, blank=True)
	category = models.CharField(max_length=100, blank=True)
	stock_level = models.PositiveIntegerField(default=0)
	low_stock_threshold = models.PositiveIntegerField(default=5)	
	price = models.DecimalField(default=0, max_digits=14, decimal_places=2)
	last_updated = models.DateTimeField(auto_now=True)


	class Meta:
		ordering = ["-last_updated"]
		constraints = [
			models.UniqueConstraint(fields=["owner", "product_name"], name="user_unique_product"),
			models.CheckConstraint(condition=Q(price__gt=0), name="price_greater_than_zero")
		]

	def __str__(self):
		return f"{self.product_name} - {self.price}"
