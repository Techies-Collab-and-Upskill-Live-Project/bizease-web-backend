from django.test import TestCase
from .models import Inventory
from .serializers import InventoryItemSerializer
from rest_framework.test import APITestCase
from datetime import datetime
from django.db.utils import IntegrityError
from accounts.models import CustomUser

# Things to Test
# Views
# - Response content and status code
# - Authenticated requests
# - Unauthenticated requests
# - creating inventory data
# - getiing inventory data & stats
# - Updating inventory data
# - deleting inventory items and it's cascading effect


class InventorySerializersTest(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.test_user = CustomUser.objects.create(
			business_name="Inventory Test Biz", full_name="Inventory test user", email="inventorytestuser@email.com", 
			business_email="inventorytestuser@testbiz.com", currency="NGN", business_phone="08134568765", business_type="Nonprofit",
			password="12345678"
		)
		cls.inventory_product = Inventory.objects.create(
			owner=cls.test_user, product_name="Backpack", description="For Carrying load", low_stock_threshold=0,
			category="utility", stock_level=55, price=35000
		)

	def test_model_instance_serialization(self):
		expected_output = {
			"id": self.inventory_product.id,
			"product_name": "Backpack", 
			"description": "For Carrying load",
			"category": "utility",
			"stock_level": 55,
			"price": "35000.00",
			"low_stock_threshold": 0,
		}
		serializer_output = InventoryItemSerializer(self.inventory_product).data
		last_updated = serializer_output.pop("last_updated")
		self.assertEqual(expected_output, serializer_output)
		self.assertRegex("2025-06-25T04:02:39.471738Z", r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{6}Z$')

	def Test_inventory_item_creation_through_serializer_without_err(self):
		data = {
			"product_name": "introduction to django ",
			"desription": "Learn web dev using django",
			"category": "ebook", "price": 15000, "stock_level": 20
		}
		item_serializer = InventoryItemSerializer(data=data)
		self.assertEqual(item_serializer.is_valid(), True)
		new_inventory_item = item_serializer.save(self.test_user)
		self.assertEqual(new_inventory_item.product_name, "Introduction To Django")
		self.assertEqual(new_inventory_item.category, "Ebook")

	def Test_inventory_item_creation_through_serializer_with_err(self):
		data = {
			"product_name": "introduction to django ",
			"desription": "Learn web dev using django",
			"category": "ebook", "price": 15000, "stock_level": 20
		}
		item_serializer = InventoryItemSerializer(data=data) 
		self.assertEqual(item_serializer.is_valid(), True)
		self.assertRaises(IntegrityError, item_serializer.save, self.test_user)

	def test_inventory_item_creation_through_serializer(self):
		self.Test_inventory_item_creation_through_serializer_without_err()
		self.Test_inventory_item_creation_through_serializer_with_err()

	def test_updating_through_serializer_without_err(self):
		item_serializer = InventoryItemSerializer(self.inventory_product, data={"product_name": "back pack", "category": "accessories"}, partial=True)
		self.assertEqual(item_serializer.is_valid(), True)
		updated_inventory_item = item_serializer.save(self.test_user)
		self.assertEqual(updated_inventory_item.product_name, "Back Pack")
		self.assertEqual(updated_inventory_item.category, "Accessories")

	def test_updating_through_serializer_with_err(self):
		existing_item = Inventory.objects.create(owner=self.test_user, product_name="Iphone X", stock_level=55, price=200000)
		item_serializer = InventoryItemSerializer(self.inventory_product, data={"product_name": "Iphone X"}, partial=True)
		self.assertEqual(item_serializer.is_valid(), True)
		self.assertRaises(IntegrityError, item_serializer.save, self.test_user)

	def test_invalid_monetary_data(self):
		data = {
			"product_name": "ENIAC", "category": "computers", 
			"price": -15000000, "stock_level": -20, "low_stock_threshold": -25
		}
		item_serializer = InventoryItemSerializer(data=data)
		self.assertEqual(item_serializer.is_valid(), False) # comeback to assert the exact errors
		# self.assertEqual(str(item_serializer.errors['stock_level'].string), 'Ensure this value is greater than or equal to 0.')
		# self.assertEqual(str(item_serializer.errors['low_stock_threshold'].string), 'Ensure this value is greater than or equal to 0.')

class InventoryViewsTest():
	pass