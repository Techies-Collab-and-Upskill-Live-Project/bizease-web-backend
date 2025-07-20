from inventory.models import Inventory
from inventory.serializers import InventoryItemSerializer
from rest_framework.test import APITransactionTestCase
from datetime import datetime
from accounts.models import CustomUser
from rest_framework_simplejwt.tokens import RefreshToken
from django.urls import reverse
from rest_framework import status
from datetime import date


class InventoryViewsTest(APITransactionTestCase):
	def setUp(self):
		self.test_user = CustomUser.objects.create(
			business_name="Business 1", full_name="Business Man", email="businessMan@email.com", password="12345678", is_active=True
		)
		self.refresh_obj = RefreshToken.for_user(self.test_user)
		self.access_token = str(self.refresh_obj.access_token)

		self.item_1 = Inventory.objects.create(owner=self.test_user, product_name="Glasses", price=10000, stock_level=15, date_added="2025-07-20")
		self.item_2 = Inventory.objects.create(owner=self.test_user, product_name="Plastic Chair", price=7000, stock_level=100, date_added="2025-07-20")
		self.item_3 = Inventory.objects.create(owner=self.test_user, product_name="Rubbish", price=0.005, stock_level=1, date_added="2025-07-20")
		self.item_4 = Inventory.objects.create(owner=self.test_user, product_name="Safety Boots", price=45000, stock_level=20, category="ppe", date_added="2025-07-20")
		self.item_5 = Inventory.objects.create(owner=self.test_user, product_name="Helmet", price=8000, stock_level=40, category="ppe", date_added="2025-07-20")
		self.item_6 = Inventory.objects.create(owner=self.test_user, product_name="Biscuits", price=100, stock_level=36, date_added="2025-07-20")

	def create_product_that_exists(self):
		response = self.client.post(reverse("inventory", args=["v1"]), 
			{"product_name": self.item_1.product_name, "stock_level": 10, "price": 100000, "date_added": "2025-07-20"}, format='json')
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertEqual(response.data["detail"], "Multiple inventory items with the same 'product_name' are not allowed")

	def create_valid_new_product(self):
		data = {"product_name": "Rice", "stock_level": 50, "price": 100000, "date_added": "2025-07-20"}
		response = self.client.post(reverse("inventory", args=["v1"]), data, format='json')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(response.data["detail"], "New Item added to inventory")
		inventory_item = Inventory.objects.get(pk=response.data["data"]["id"])
		self.assertEqual("Rice", inventory_item.product_name)
		self.assertEqual(50, inventory_item.stock_level)
		self.assertEqual(100000, inventory_item.price)

	def create_new_product_with_missing_fields(self):
		data = {"stock_level": 50, "price": 100000}
		response = self.client.post(reverse("inventory", args=["v1"]), data, format='json')
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertEqual(response.data["detail"]["product_name"], ["This field is required."])
		self.assertEqual(response.data["detail"]["date_added"], ["This field is required."])

	def test_create_inventory_items_with_credentials(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		self.create_product_that_exists()
		self.create_valid_new_product()
		self.create_new_product_with_missing_fields()

	def test_create_inventory_items_without_credentials(self):
		data = {"product_name": "product-1", "stock_level": 5, "price": 800, "date_added": "2025-07-20"} 
		response = self.client.post(reverse("inventory", args=["v1"]), data, format='json')
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_authenticated_get_inventory_items_by_category(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		response = self.client.get(reverse("inventory", args=["v1"]), query_params={"category": "ppe"}, format='json')
		self.assertEqual(response.data["data"]["length"], 2)
		self.assertEqual(response.data["data"]["products"][0]["product_name"], "Helmet")
		self.assertEqual(response.data["data"]["products"][1]["product_name"], "Safety Boots")
		self.assertEqual(response.status_code, status.HTTP_200_OK)

	def test_authenticated_get_inventory_items_order_by_id(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		orderedItems = Inventory.objects.filter(owner=self.test_user).order_by("id")

		response = self.client.get(reverse("inventory", args=["v1"]), query_params={"order": "id"}, format='json')
		self.assertEqual(response.data["data"]["length"], 6)
		self.assertEqual(response.data["data"]["products"][0]["product_name"], orderedItems.first().product_name)
		self.assertEqual(response.data["data"]["products"][5]["product_name"], orderedItems.last().product_name)
		self.assertEqual(response.status_code, status.HTTP_200_OK)

		response = self.client.get(reverse("inventory", args=["v1"]), query_params={"order": "-id"}, format='json')
		self.assertEqual(response.data["data"]["length"], 6)
		self.assertEqual(response.data["data"]["products"][0]["product_name"], orderedItems.last().product_name)
		self.assertEqual(response.data["data"]["products"][5]["product_name"], orderedItems.first().product_name)
		self.assertEqual(response.status_code, status.HTTP_200_OK)

	def test_authenticated_get_inventory_items_order_by_price(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)

		response = self.client.get(reverse("inventory", args=["v1"]), query_params={"order": "price"}, format='json')
		self.assertEqual(response.data["data"]["length"], 6)
		self.assertEqual(response.data["data"]["products"][0]["product_name"], "Rubbish")
		self.assertEqual(response.data["data"]["products"][5]["product_name"], "Safety Boots")
		self.assertEqual(response.status_code, status.HTTP_200_OK)

		response = self.client.get(reverse("inventory", args=["v1"]), query_params={"order": "-price"}, format='json')
		self.assertEqual(response.data["data"]["length"], 6)
		self.assertEqual(response.data["data"]["products"][0]["product_name"], "Safety Boots")
		self.assertEqual(response.data["data"]["products"][5]["product_name"], "Rubbish")
		self.assertEqual(response.status_code, status.HTTP_200_OK)

	def test_authenticated_get_inventory_items_order_by_last_updated(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		orderedItems = Inventory.objects.filter(owner=self.test_user).order_by("last_updated")

		response = self.client.get(reverse("inventory", args=["v1"]), query_params={"order": "last_updated"}, format='json')
		self.assertEqual(response.data["data"]["length"], 6)
		self.assertEqual(response.data["data"]["products"][0]["product_name"], orderedItems.first().product_name)
		self.assertEqual(response.data["data"]["products"][5]["product_name"], orderedItems.last().product_name)
		self.assertEqual(response.status_code, status.HTTP_200_OK)

		response = self.client.get(reverse("inventory", args=["v1"]), query_params={"order": "-last_updated"}, format='json')
		self.assertEqual(response.data["data"]["length"], 6)
		self.assertEqual(response.data["data"]["products"][0]["product_name"], orderedItems.last().product_name)
		self.assertEqual(response.data["data"]["products"][5]["product_name"], orderedItems.first().product_name)
		self.assertEqual(response.status_code, status.HTTP_200_OK)

	def test_authenticated_get_inventory_items_with_lowstock(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		response = self.client.get(reverse("inventory", args=["v1"]), query_params={"low_stock": ""}, format='json')
		self.assertEqual(response.data["data"]["length"], 1)
		self.assertEqual(response.data["data"]["products"][0]["product_name"], "Rubbish")
		self.assertEqual(response.status_code, status.HTTP_200_OK)

	def test_get_inventory_items_with_credentials(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		response = self.client.get(reverse("inventory", args=["v1"]))
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["data"]["page_count"], 1)
		self.assertEqual(response.data["data"]["next_page"], None)
		self.assertEqual(response.data["data"]["prev_page"], None)
		self.assertEqual(response.data["data"]["length"], Inventory.objects.count())
		self.assertEqual(response.data["data"]["products"][0]["product_name"], "Biscuits")
		self.assertEqual(response.data["data"]["products"][1]["product_name"], "Helmet")
		self.assertEqual(response.data["data"]["products"][2]["product_name"], "Safety Boots")

	def test_get_inventory_items_without_credentials(self):
		response = self.client.get(reverse("inventory", args=["v1"]))
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_get_single_inventory_item_with_credentials(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		response = self.client.get(reverse("inventory-item", args=["v1", str(self.item_1.id)]))
		# print(response.data)
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
			"date_added": "2025-06-09"
		}
		response = self.client.put(reverse("inventory-item", args=["v1", str(self.item_2.id)]), update_payload, format='json')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.item_2 = Inventory.objects.get(pk=self.item_2.id)
		expected_data = {**update_payload}
		expected_data["product_name"] = "New Name" # The text would have been normalized 
		expected_data["last_updated"] = self.item_2.last_updated.isoformat().replace('+00:00', 'Z') # This field is automatically updated
		expected_data["price"] = f"{expected_data['price']:.2f}"
		expected_data["category"] = ""
		expected_data["id"] = self.item_2.id # This field can't be updated
		expected_data["date_added"] = "2025-06-09" # This field can't be updated

		self.assertEqual(InventoryItemSerializer(self.item_2).data, expected_data)

	def update_item_with_invalid_data(self):
		update_payload = {
			"product_name": "Glasses",
		}
		response = self.client.put(reverse("inventory-item", args=["v1", str(self.item_2.id)]), update_payload, format='json')
		self.assertEqual(response.data["detail"], "Multiple inventory items with the same 'product_name' are not allowed")
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

		update_payload = {
			"price": -1,
			"date_added": "2025-y6-09"
		}
		response = self.client.put(reverse("inventory-item", args=["v1", str(self.item_1.id)]), update_payload, format='json')
		self.assertEqual(response.data["detail"]["price"], ["Ensure this value is greater than or equal to 0."])
		self.assertEqual(response.data["detail"]["date_added"], ["Date has wrong format. Use one of these formats instead: YYYY-MM-DD."])
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

	def update_nonexistent_inventory_item(self):
		update_payload = {
			"product_name": "Dont matter",
		}
		response = self.client.put(reverse("inventory-item", args=["v1", "99999999999"]), update_payload, format='json')
		self.assertEqual(response.data["detail"], "Item not found")
		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


	def test_update_single_inventory_item_with_credentials(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		self.update_item_with_valid_data()
		self.update_item_with_invalid_data()
		self.update_nonexistent_inventory_item()

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