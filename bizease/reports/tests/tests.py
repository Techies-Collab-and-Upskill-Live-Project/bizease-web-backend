from rest_framework.test import APITransactionTestCase
from orders.models import Order, OrderedProduct
from accounts.models import CustomUser
from inventory.models import Inventory
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import date


class ReportsViewsTest(APITransactionTestCase):
	def setUp(self):
		self.test_user = CustomUser.objects.create(
			business_name="Random sales llc", full_name="Random User", email="randomuser@gmail.com", password="12345678", is_active=True
		)
		self.refresh_obj = RefreshToken.for_user(self.test_user)
		self.access_token = str(self.refresh_obj.access_token)

		self.item_1 = Inventory.objects.create(owner=self.test_user, product_name="Safety Boots", price=65000, stock_level=20, date_added="2024-04-22")
		self.item_2 = Inventory.objects.create(owner=self.test_user, product_name="Helmet", price=6000, stock_level=45, date_added="2024-05-20")
		self.item_3 = Inventory.objects.create(owner=self.test_user, product_name="Tape", price=4000, stock_level=60, date_added="2024-07-17")
		self.item_4 = Inventory.objects.create(owner=self.test_user, product_name="Wheelbarrow", price=150000, stock_level=7, low_stock_threshold=10, date_added="2024-09-20")

		self.order = Order(product_owner_id=self.test_user, client_name="bob", client_email="bob@gmail.com", order_date="2025-03-10")
		self.order.ordered_products_objects = [OrderedProduct(name="Wheelbarrow", quantity=1, price=150000), OrderedProduct(name="Helmet", quantity=5, price=6000)]
		self.order.save()

		self.order_1 = Order(product_owner_id=self.test_user, client_name="Davy Jones", client_email="dv@shipwrecks.ocean", status="Delivered", order_date="2025-03-20")
		self.order_1.ordered_products_objects = [OrderedProduct(name="Wheelbarrow", quantity=1, price=150000)]
		self.order_1.save()

		self.order_2 = Order(product_owner_id=self.test_user, client_name="customer 1", client_phone="08045342896", status="Delivered", order_date="2024-12-02")
		self.order_2.ordered_products_objects = [
			OrderedProduct(name="Helmet", quantity=10, price=6000), 
			OrderedProduct(name="Tape", quantity=4, price=4000), 
			OrderedProduct(name="Safety Boots", quantity=2, price=65000)
		]
		self.order_2.save()

		self.order_2 = Order(product_owner_id=self.test_user, client_name="customer 2", order_date="2024-10-20")
		self.order_2.ordered_products_objects = [
			OrderedProduct(name="Wheelbarrow", quantity=1, price=150000),
			OrderedProduct(name="Safety Boots", quantity=1, price=65000)
		]
		self.order_2.save()

	def test_get_reports_without_credentials(self):
		response = self.client.get(reverse("reports", args=["v1"]), format="json")
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_get_all_time_reports_with_credentials(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		response = self.client.get(reverse("reports", args=["v1"]), format="json")

		self.assertEqual(response.data["data"]["period"], "All time")
		self.assertEqual(response.data["data"]["top_selling_product"], "Helmet")
		self.assertEqual(response.data["data"]["low_stock_items"], 1)
		self.assertEqual(response.data["data"]["pending_orders"], 2)
		self.assertEqual(response.data["data"]["total_products"], 4)
		self.assertEqual(response.data["data"]["total_stock_value"], 2109000)
		self.assertEqual(response.data["data"]["total_revenue"], 751000)
		print(response.data["data"]["date_revenue_chart_data"])
		self.assertEqual(response.data["data"]["date_revenue_chart_data"][0]["revenue"], 150000)
		self.assertEqual(response.data["data"]["date_revenue_chart_data"][0]["date"], date.fromisoformat("2025-03-20"))
		self.assertIn({"name": "Helmet", "quantity_sold": 15}, response.data["data"]["product_sales_chart_data"])
		self.assertIn({"name": "Safety Boots", "quantity_sold": 3}, response.data["data"]["product_sales_chart_data"])
		self.assertIn({"name": "Tape", "quantity_sold": 4}, response.data["data"]["product_sales_chart_data"])
		self.assertIn({"name": "Wheelbarrow", "quantity_sold": 3}, response.data["data"]["product_sales_chart_data"])
		self.assertEqual(response.status_code, status.HTTP_200_OK)

	def test_get_reports_summary_without_credentials(self):
		response = self.client.get(reverse("reports-summary", args=["v1"]), format="json")
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_get_all_time_reports_summary_with_credentials(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		response = self.client.get(reverse("reports-summary", args=["v1"]), format="json")

		self.assertEqual(response.data["data"]["period"], "All time")
		self.assertIn({'name': 'Helmet', 'quantity_sold': 15, 'revenue': 90000.00, 'stock_status': 'in stock'}, response.data["data"]["summary"])
		self.assertIn({'name': 'Safety Boots', 'quantity_sold': 3, 'revenue': 195000.00, 'stock_status': 'in stock'}, response.data["data"]["summary"])
		self.assertIn({'name': 'Tape', 'quantity_sold': 4, 'revenue': 16000.00, 'stock_status': 'in stock'}, response.data["data"]["summary"])
		self.assertIn({'name': 'Wheelbarrow', 'quantity_sold': 3, 'revenue': 450000.00, 'stock_status': 'low stock'}, response.data["data"]["summary"])

		self.assertEqual(response.status_code, status.HTTP_200_OK)
