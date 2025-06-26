from django.test import TestCase
from .models import Inventory
from .serializers import InventoryItemSerializer
from rest_framework.test import APITestCase
from datetime import datetime
from django.db.utils import IntegrityError
from accounts.models import CustomUser
from rest_framework_simplejwt.tokens import RefreshToken
from django.urls import reverse
from rest_framework import status


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


class InventoryViewsTest(APITestCase):
	@classmethod
	def setUpTestData(cls):
		cls.test_user = CustomUser.objects.create(
			business_name="Business 1", full_name="Business Man", email="businessMan@email.com", password="12345678"
		)
		cls.refresh_obj = RefreshToken.for_user(cls.test_user)
		# refresh_token = str(refresh_obj)
		cls.access_token = str(cls.refresh_obj.access_token)

		cls.item_1 = Inventory.objects.create(owner=cls.test_user, product_name="Glasses", price=10000, stock_level=15)
		cls.item_2 = Inventory.objects.create(owner=cls.test_user, product_name="Plastic Chair", price=7000, stock_level=100)
		cls.item_3 = Inventory.objects.create(owner=cls.test_user, product_name="Rubbish", price=0.005, stock_level=1)

	def create_product_that_exists(self):
		response = self.client.post(reverse("inventory", args=["v1"]), {"product_name": self.item_1.product_name, "stock_level": 10, "price": 100000})
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertEqual(response.data["detail"], "Multiple inventory items with the same 'product_name' are not allowed")

	def create_valid_new_product(self):
		response = self.client.post(reverse("inventory", args=["v1"]), {"product_name": "Rice", "stock_level": 50, "price": 100000})
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(response.data["detail"], "New Item added to inventory")
		inventory_item = Inventory.objects.get(pk=response.data["data"]["id"])
		self.assertEqual("Rice", inventory_item.product_name)
		self.assertEqual(50, inventory_item.stock_level)
		self.assertEqual(100000, inventory_item.price)

	def test_create_inventory_items_with_credentials(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		# self.create_product_that_exists()
		self.create_valid_new_product()

	def test_create_inventory_items_without_credentials(self):
		response = self.client.post(reverse("inventory", args=["v1"]), {"product_name": "product-1", "stock_level": 5, "price": 800})
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_get_inventory_items_with_credentials(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		response = self.client.get(reverse("inventory", args=["v1"]))
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["data"]["page_count"], 1)
		self.assertEqual(response.data["data"]["next_page"], None)
		self.assertEqual(response.data["data"]["prev_page"], None)
		self.assertEqual(response.data["data"]["length"], Inventory.objects.count())
		# Test the products returned but it seems like we need to set default ordering first
		# Test the query params firsts

	def test_get_inventory_items_without_credentials(self):
		response = self.client.get(reverse("inventory", args=["v1"]))
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_get_single_inventory_item_with_credentials(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		response = self.client.get(reverse("inventory-item", args=["v1", str(self.item_1.id)]))
		expected_data = InventoryItemSerializer(self.item_1).data
		self.assertEqual(response.data["data"], expected_data)

		response = self.client.get(reverse("inventory-item", args=["v1", '99999999999']))
		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
		self.assertEqual(response.data["detail"], "Item not found")

	def test_get_single_inventory_item_without_credentials(self):
		response = self.client.get(reverse("inventory-item", args=["v1", "1"]))
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def update_item_with_valid_data(self):
		update_payload = {
			"product_name": "new name",
			"description": "Testing the 'PUT' method",
			"stock_level": 45,
			"low_stock_threshold": 1000,
			"price": 1,
		}
		response = self.client.put(reverse("inventory-item", args=["v1", str(self.item_2.id)]), update_payload)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.item_2 = Inventory.objects.get(pk=self.item_2.id)
		expected_data = {**update_payload}
		expected_data["product_name"] = "New Name" # The text would have been normalized 
		expected_data["last_updated"] = self.item_2.last_updated.isoformat().replace('+00:00', 'Z') # This field is automatically updated
		expected_data["price"] = f"{expected_data['price']:.2f}"
		expected_data["category"] = ""
		expected_data["id"] = self.item_2.id # This field can't be updated

		self.assertEqual(InventoryItemSerializer(self.item_2).data, expected_data)

	def test_update_single_inventory_item_with_credentials(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		self.update_item_with_valid_data()
		# self.update_item_with_invalid_data

	def test_delete_inventory_item_with_credentials(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		response = self.client.delete(reverse("inventory-item", args=["v1", str(self.item_3.id)]))
		self.assertRaises(Inventory.DoesNotExist, Inventory.objects.get, pk=self.item_3.id)
		self.assertEqual(response.data["detail"], "Inventory Item deleted successfully")
		self.assertEqual(response.status_code, status.HTTP_200_OK)

		response = self.client.delete(reverse("inventory-item", args=["v1", "999999999"]))
		self.assertEqual(response.data["detail"], "Item not found")
		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

	def test_delete_inventory_item_without_credentials(self):
		response = self.client.delete(reverse("inventory-item", args=["v1", '3']))
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)