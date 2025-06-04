from django.db import models
from accounts.models import CustomUser

class Category(models.Model):
	owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
	name = models.CharField(max_length=100, unique=True)

	class Meta:
		constraints = [models.UniqueConstraint(fields=["owner", "name"], name="user_unique_category")]


class Inventory(models.Model):
	owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
	product_name = models.CharField(max_length=100)
	description = models.CharField(max_length=300, blank=True)
	category = models.ForeignKey(Category, to_field="name", on_delete=models.SET_NULL, null=True)
	stock_level = models.IntegerField(default=0) # Add a check constraint that rejects negative numbers
	price = models.IntegerField(default=0) # Add a check constraint that rejects negative numbers
	last_updated = models.DateField(auto_now_add=True)


	class Meta:
		ordering = ["-last_updated"]

	def __str__(self):
		return f"{self.product_name} - {self.price}"
