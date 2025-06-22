from django.db import models
from accounts.models import CustomUser

class Inventory(models.Model):
	owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
	product_name = models.CharField(max_length=100, unique=True)
	description = models.CharField(max_length=300, blank=True)
	category = models.CharField(max_length=100, blank=True)
	stock_level = models.PositiveIntegerField(default=0)
	low_stock_threshold = models.PositiveIntegerField(default=5)
	price = models.PositiveIntegerField(default=0)
	last_updated = models.DateField(auto_now_add=True)


	class Meta:
		ordering = ["-last_updated"]

	def __str__(self):
		return f"{self.product_name} - {self.price}"
