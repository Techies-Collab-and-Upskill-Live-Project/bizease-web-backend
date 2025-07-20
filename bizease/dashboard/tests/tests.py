from rest_framework.test import APITransactionTestCase
from orders.models import Order, OrderedProduct
from accounts.models import CustomUser
from inventory.models import Inventory
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken


class DashboardViewTest(APITransactionTestCase):
	def setUp(self):
		self.test_user = CustomUser.objects.create(
			business_name="Random sales llc", full_name="Random User", email="randomuser@gmail.com", password="12345678", is_active=True, currency="USD"
		)
		self.refresh_obj = RefreshToken.for_user(self.test_user)
		self.access_token = str(self.refresh_obj.access_token)

		self.item_1 = Inventory.objects.create(owner=self.test_user, product_name="Safety Boots", price=65000, stock_level=20)
		self.item_2 = Inventory.objects.create(owner=self.test_user, product_name="Helmet", price=6000, stock_level=45)
		self.item_3 = Inventory.objects.create(owner=self.test_user, product_name="Tape", price=4000, stock_level=60)
		self.item_4 = Inventory.objects.create(owner=self.test_user, product_name="Wheelbarrow", price=150000, stock_level=7, low_stock_threshold=10)

		self.order = Order(product_owner_id=self.test_user, client_name="bob", client_email="bob@gmail.com")
		self.order.ordered_products_objects = [OrderedProduct(name="Wheelbarrow", quantity=1, price=150000), OrderedProduct(name="Helmet", quantity=5, price=6000)]
		self.order.save()

		self.order_1 = Order(product_owner_id=self.test_user, client_name="Davy Jones", client_email="dv@shipwrecks.ocean", status="Delivered")
		self.order_1.ordered_products_objects = [OrderedProduct(name="Wheelbarrow", quantity=1, price=150000)]
		self.order_1.save()

		self.order_2 = Order(product_owner_id=self.test_user, client_name="customer 1", client_phone="08045342896", status="Delivered")
		self.order_2.ordered_products_objects = [
			OrderedProduct(name="Helmet", quantity=10, price=6000), 
			OrderedProduct(name="Tape", quantity=4, price=4000), 
			OrderedProduct(name="Safety Boots", quantity=2, price=65000)
		]
		self.order_2.save()

		self.order_2 = Order(product_owner_id=self.test_user, client_name="customer 2")
		self.order_2.ordered_products_objects = [
			OrderedProduct(name="Wheelbarrow", quantity=1, price=150000),
			OrderedProduct(name="Safety Boots", quantity=1, price=65000)
		]
		self.order_2.save()

	def test_get_dashboard_data_without_credentials(self):
		response = self.client.get(reverse("dashboard-data", args=["v1"]), format="json")
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_get_all_time_dashboard_data_with_credentials(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		response = self.client.get(reverse("dashboard-data", args=["v1"]), format="json")

		self.assertEqual(response.data["data"]["business_name"], "Random sales llc")
		self.assertEqual(response.data["data"]["currency"], "USD")
		self.assertEqual(response.data["data"]["top_selling_product"], "Helmet")
		self.assertEqual(response.data["data"]["revenue"], 751000)
		self.assertEqual(response.data["data"]["language"], "English")
		self.assertEqual(len(response.data["data"]["pending_orders"]), 2)
		self.assertEqual(response.data["data"]["pending_orders"][0]["client_name"], "customer 2")
		self.assertEqual(response.data["data"]["pending_orders"][1]["client_name"], "bob")
		self.assertEqual(len(response.data["data"]["low_stock_items"]), 1)
		self.assertEqual(response.data["data"]["low_stock_items"][0]["product_name"], "Wheelbarrow")

		self.assertEqual(response.status_code, status.HTTP_200_OK)
