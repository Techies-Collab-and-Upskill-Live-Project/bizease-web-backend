from rest_framework.test import APITransactionTestCase
from orders.models import Order, OrderedProduct
from accounts.models import CustomUser
from inventory.models import Inventory
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import date, datetime
from unittest.mock import patch
from decimal import Decimal

class mock_django_timezone(datetime):
	@classmethod
	def now(cls):
		return datetime(2025, 3, 20)

class ReportsViewsTest(APITransactionTestCase):
	def setUp(self):
		self.test_user = CustomUser.objects.create(
			business_name="Random sales llc", full_name="Random User", email="randomuser@gmail.com", password="12345678", is_active=True
		)
		self.refresh_obj = RefreshToken.for_user(self.test_user)
		self.access_token = str(self.refresh_obj.access_token)

		self.item_1 = Inventory.objects.create(owner=self.test_user, product_name="Safety Boots", price=65000, stock_level=20, date_added="2025-04-22")
		self.item_2 = Inventory.objects.create(owner=self.test_user, product_name="Helmet", price=6000, stock_level=45, date_added="2025-05-20")
		self.item_3 = Inventory.objects.create(owner=self.test_user, product_name="Tape", price=4000, stock_level=60, date_added="2024-07-17")
		self.item_4 = (
			Inventory.objects.create(owner=self.test_user, product_name="Wheelbarrow", price=150000, stock_level=7, low_stock_threshold=10, date_added="2024-09-20")
		)

		self.order = Order(product_owner_id=self.test_user, client_name="bob", client_email="bob@gmail.com", order_date="2025-03-14")
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


	def test_get_reports_without_credentials(self):
		response = self.client.get(reverse("reports", args=["v1"]), format="json")
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_get_all_time_reports_with_credentials(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		response = self.client.get(reverse("reports", args=["v1"]), format="json")

		self.assertEqual(response.data["data"]["period"], "All time")
		self.assertEqual(response.data["data"]["top_selling_product"], "Helmet")
		self.assertEqual(response.data["data"]["low_stock_items"], 1)
		self.assertEqual(response.data["data"]["pending_orders"], 1)
		self.assertEqual(response.data["data"]["total_products"], 4)
		self.assertEqual(response.data["data"]["total_stock_value"], 2324000)
		self.assertEqual(response.data["data"]["stock_value_change"], None)
		self.assertEqual(response.data["data"]["total_revenue"], 356000)
		self.assertEqual(response.data["data"]["revenue_change"], None)
		self.assertEqual(len(response.data["data"]["date_revenue_chart_data"]), 2)
		self.assertEqual(response.data["data"]["date_revenue_chart_data"][0]["revenue"], 150000)
		self.assertEqual(response.data["data"]["date_revenue_chart_data"][0]["date"], date.fromisoformat("2025-03-20"))
		self.assertIn({"name": "Helmet", "quantity_sold": 10}, response.data["data"]["product_sales_chart_data"])
		self.assertIn({"name": "Safety Boots", "quantity_sold": 2}, response.data["data"]["product_sales_chart_data"])
		self.assertIn({"name": "Tape", "quantity_sold": 4}, response.data["data"]["product_sales_chart_data"])
		self.assertIn({"name": "Wheelbarrow", "quantity_sold": 1}, response.data["data"]["product_sales_chart_data"])
		self.assertEqual(response.status_code, status.HTTP_200_OK)

	def test_get_reports_summary_without_credentials(self):
		response = self.client.get(reverse("reports-summary", args=["v1"]), format="json")
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_get_all_time_reports_summary_with_credentials(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		response = self.client.get(reverse("reports-summary", args=["v1"]), format="json")

		self.assertEqual(response.data["data"]["period"], "All time")
		self.assertIn({'name': 'Helmet', 'quantity_sold': 10, 'revenue': 60000.00, 'stock_status': 'in stock'}, response.data["data"]["summary"])
		self.assertIn({'name': 'Safety Boots', 'quantity_sold': 2, 'revenue': 130000.00, 'stock_status': 'in stock'}, response.data["data"]["summary"])
		self.assertIn({'name': 'Tape', 'quantity_sold': 4, 'revenue': 16000.00, 'stock_status': 'in stock'}, response.data["data"]["summary"])
		self.assertIn({'name': 'Wheelbarrow', 'quantity_sold': 1, 'revenue': 150000.00, 'stock_status': 'low stock'}, response.data["data"]["summary"])

		self.assertEqual(response.status_code, status.HTTP_200_OK)

	@patch("reports.views.timezone", mock_django_timezone)
	def test_get_last_week_reports_with_credentials(self):
		Inventory.objects.create(owner=self.test_user, product_name="Jacket", price=65000, stock_level=20, date_added="2025-03-20")
		self.order_week_b4_last = (
			Order(product_owner_id=self.test_user, client_name="Davy Jones", client_email="dv@shipwrecks.ocean", status="Delivered", order_date="2025-03-12")
		)
		self.order_week_b4_last.ordered_products_objects = [
			OrderedProduct(name="Tape", quantity=1, price=4000), 
			OrderedProduct(name="Safety Boots", quantity=2, price=65000)
		]
		self.order_week_b4_last.save()

		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		response = self.client.get(reverse("reports", args=["v1"]), query_params={"period": "last-week"}, format="json")

		self.assertEqual(response.data["data"]["period"], "last-week")
		self.assertEqual(response.data["data"]["top_selling_product"], "Wheelbarrow")
		self.assertEqual(response.data["data"]["low_stock_items"], 1)
		self.assertEqual(response.data["data"]["pending_orders"], 1)
		self.assertEqual(response.data["data"]["total_products"], 5)
		self.assertEqual(response.data["data"]["total_stock_value"], 2270000)
		self.assertEqual(response.data["data"]["stock_value_change"], Decimal('134.02'))
		self.assertEqual(response.data["data"]["total_revenue"], 150000)
		self.assertEqual(response.data["data"]["revenue_change"], Decimal('11.94'))
		self.assertEqual(len(response.data["data"]["date_revenue_chart_data"]), 1)
		self.assertEqual(response.data["data"]["date_revenue_chart_data"][0]["revenue"], 150000)
		self.assertEqual(response.data["data"]["date_revenue_chart_data"][0]["date"], date.fromisoformat("2025-03-20"))
		self.assertEqual([{"name": "Wheelbarrow", "quantity_sold": 1}], list(response.data["data"]["product_sales_chart_data"]))
		self.assertEqual(response.status_code, status.HTTP_200_OK)

	@patch("reports.views.timezone", mock_django_timezone)
	def test_get_last_month_reports_with_credentials(self):
		self.order_month_b4_last = (
			Order(product_owner_id=self.test_user, client_name="Davy Jones", client_email="dv@shipwrecks.ocean", status="Delivered", order_date="2025-02-07")
		)
		self.order_month_b4_last.ordered_products_objects = [
			OrderedProduct(name="Wheelbarrow", quantity=1, price=150000),
			OrderedProduct(name="Safety Boots", quantity=1, price=65000)
		]
		self.order_month_b4_last.save()

		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		response = self.client.get(reverse("reports", args=["v1"]), query_params={"period": "last-month"}, format="json")

		self.assertEqual(response.data["data"]["period"], "last-month")
		self.assertEqual(response.data["data"]["top_selling_product"], "Wheelbarrow")
		self.assertEqual(response.data["data"]["low_stock_items"], 1)
		self.assertEqual(response.data["data"]["pending_orders"], 1)
		self.assertEqual(response.data["data"]["total_products"], 4)
		self.assertEqual(response.data["data"]["total_stock_value"], 824000)
		self.assertEqual(response.data["data"]["stock_value_change"], Decimal('0.00'))
		self.assertEqual(response.data["data"]["total_revenue"], 150000)
		self.assertEqual(response.data["data"]["revenue_change"], Decimal('-30.23'))
		self.assertEqual(len(response.data["data"]["date_revenue_chart_data"]), 1)
		self.assertEqual(response.data["data"]["date_revenue_chart_data"][0]["revenue"], 150000)
		self.assertEqual(response.data["data"]["date_revenue_chart_data"][0]["date"], date.fromisoformat("2025-03-20"))
		self.assertEqual([{"name": "Wheelbarrow", "quantity_sold": 1}], list(response.data["data"]["product_sales_chart_data"]))
		self.assertEqual(response.status_code, status.HTTP_200_OK)

	@patch("reports.views.timezone", mock_django_timezone)
	def test_get_last_6_months_with_credentials(self):
		self.order_month_b4_last = (
			Order(product_owner_id=self.test_user, client_name="Davy Jones", client_email="dv@shipwrecks.ocean", status="Delivered", order_date="2024-05-07")
		)
		self.order_month_b4_last.ordered_products_objects = [
			OrderedProduct(name="Safety Boots", quantity=3, price=65000),
		]
		self.order_month_b4_last.save()

		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		response = self.client.get(reverse("reports", args=["v1"]), query_params={"period": "last-6-months"}, format="json")

		self.assertEqual(response.data["data"]["period"], "last-6-months")
		self.assertEqual(response.data["data"]["top_selling_product"], "Helmet")
		self.assertEqual(response.data["data"]["low_stock_items"], 1)
		self.assertEqual(response.data["data"]["pending_orders"], 1)
		self.assertEqual(response.data["data"]["total_products"], 4)
		self.assertEqual(response.data["data"]["total_stock_value"], 974000)
		self.assertEqual(response.data["data"]["total_revenue"], 356000)
		self.assertEqual(response.data["data"]["stock_value_change"], None)
		self.assertEqual(response.data["data"]["revenue_change"], Decimal('82.56'))
		self.assertEqual(len(response.data["data"]["date_revenue_chart_data"]), 2)
		self.assertEqual(response.data["data"]["date_revenue_chart_data"][0]["revenue"], 150000)
		self.assertEqual(response.data["data"]["date_revenue_chart_data"][0]["date"], date.fromisoformat("2025-03-20"))
		self.assertIn({"name": "Helmet", "quantity_sold": 10}, response.data["data"]["product_sales_chart_data"])
		self.assertIn({"name": "Safety Boots", "quantity_sold": 2}, response.data["data"]["product_sales_chart_data"])
		self.assertIn({"name": "Tape", "quantity_sold": 4}, response.data["data"]["product_sales_chart_data"])
		self.assertIn({"name": "Wheelbarrow", "quantity_sold": 1}, response.data["data"]["product_sales_chart_data"])
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.status_code, status.HTTP_200_OK)

	@patch("reports.views.timezone", mock_django_timezone)
	def test_get_last_year_reports_with_credentials(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		response = self.client.get(reverse("reports", args=["v1"]), query_params={"period": "last-year"}, format="json")

		self.assertEqual(response.data["data"]["period"], "last-year")
		self.assertEqual(response.data["data"]["top_selling_product"], "Helmet")
		self.assertEqual(response.data["data"]["low_stock_items"], 1)
		self.assertEqual(response.data["data"]["pending_orders"], 1)
		self.assertEqual(response.data["data"]["total_products"], 4)
		self.assertEqual(response.data["data"]["total_stock_value"], 974000)
		self.assertEqual(response.data["data"]["stock_value_change"], None)
		self.assertEqual(response.data["data"]["total_revenue"], 356000)
		self.assertEqual(response.data["data"]["revenue_change"],  None)
		self.assertEqual(len(response.data["data"]["date_revenue_chart_data"]), 2)
		self.assertEqual(response.data["data"]["date_revenue_chart_data"][0]["revenue"], 150000)
		self.assertEqual(response.data["data"]["date_revenue_chart_data"][0]["date"], date.fromisoformat("2025-03-20"))
		self.assertIn({"name": "Helmet", "quantity_sold": 10}, response.data["data"]["product_sales_chart_data"])
		self.assertIn({"name": "Safety Boots", "quantity_sold": 2}, response.data["data"]["product_sales_chart_data"])
		self.assertIn({"name": "Tape", "quantity_sold": 4}, response.data["data"]["product_sales_chart_data"])
		self.assertIn({"name": "Wheelbarrow", "quantity_sold": 1}, response.data["data"]["product_sales_chart_data"])
		self.assertEqual(response.status_code, status.HTTP_200_OK)

	@patch("reports.views.timezone", mock_django_timezone)
	def test_get_last_week_reports_summary_with_credentials(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		response = self.client.get(reverse("reports-summary", args=["v1"]), query_params={"period": "last-week"}, format="json")

		self.assertEqual(response.data["data"]["period"], "last-week")
		self.assertEqual(1, len(response.data["data"]["summary"]))
		self.assertEqual({'name': 'Wheelbarrow', 'quantity_sold': 1, 'revenue': 150000.00, 'stock_status': 'low stock'}, response.data["data"]["summary"][0])
		self.assertEqual(response.status_code, status.HTTP_200_OK)

	@patch("reports.views.timezone", mock_django_timezone)
	def test_get_last_month_reports_summary_with_credentials(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		response = self.client.get(reverse("reports-summary", args=["v1"]), query_params={"period": "last-month"}, format="json")

		self.assertEqual(1, len(response.data["data"]["summary"]))
		self.assertEqual({'name': 'Wheelbarrow', 'quantity_sold': 1, 'revenue': 150000.00, 'stock_status': 'low stock'}, response.data["data"]["summary"][0])
		self.assertEqual(response.data["data"]["period"], "last-month")
		self.assertEqual(response.status_code, status.HTTP_200_OK)

	@patch("reports.views.timezone", mock_django_timezone)
	def test_get_last_6_months_reports_summary_with_credentials(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		response = self.client.get(reverse("reports-summary", args=["v1"]), query_params={"period": "last-6-months"}, format="json")

		self.assertEqual(response.data["data"]["period"], "last-6-months")
		self.assertIn({'name': 'Helmet', 'quantity_sold': 10, 'revenue': 60000.00, 'stock_status': 'in stock'}, response.data["data"]["summary"])
		self.assertIn({'name': 'Safety Boots', 'quantity_sold': 2, 'revenue': 130000.00, 'stock_status': 'in stock'}, response.data["data"]["summary"])
		self.assertIn({'name': 'Tape', 'quantity_sold': 4, 'revenue': 16000.00, 'stock_status': 'in stock'}, response.data["data"]["summary"])
		self.assertIn({'name': 'Wheelbarrow', 'quantity_sold': 1, 'revenue': 150000.00, 'stock_status': 'low stock'}, response.data["data"]["summary"])
		self.assertEqual(response.status_code, status.HTTP_200_OK)

	@patch("reports.views.timezone", mock_django_timezone)
	def test_get_last_year_reports_summary_with_credentials(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		response = self.client.get(reverse("reports-summary", args=["v1"]), query_params={"period": "last-year"}, format="json")

		self.assertEqual(response.data["data"]["period"], "last-year")
		self.assertIn({'name': 'Helmet', 'quantity_sold': 10, 'revenue': 60000.00, 'stock_status': 'in stock'}, response.data["data"]["summary"])
		self.assertIn({'name': 'Safety Boots', 'quantity_sold': 2, 'revenue': 130000.00, 'stock_status': 'in stock'}, response.data["data"]["summary"])
		self.assertIn({'name': 'Tape', 'quantity_sold': 4, 'revenue': 16000.00, 'stock_status': 'in stock'}, response.data["data"]["summary"])
		self.assertIn({'name': 'Wheelbarrow', 'quantity_sold': 1, 'revenue': 150000.00, 'stock_status': 'low stock'}, response.data["data"]["summary"])
		self.assertEqual(response.status_code, status.HTTP_200_OK)
