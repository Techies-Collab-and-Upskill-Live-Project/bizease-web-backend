from rest_framework.test import APITransactionTestCase
from orders.models import Order, OrderedProduct
from orders.serializers import OrderSerializer
from accounts.models import CustomUser
from inventory.models import Inventory
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import date


class OrdersViewsTest(APITransactionTestCase):
	def setUp(self):
		self.test_user = CustomUser.objects.create(
			business_name="user-biz", full_name="test user", email="testuser123@gmail.com", password="12345678", is_active=True
		)
		self.refresh_obj = RefreshToken.for_user(self.test_user)
		self.access_token = str(self.refresh_obj.access_token)

		self.item_1 = Inventory.objects.create(owner=self.test_user, product_name="Calculator", price=10000, stock_level=100, date_added="2025-05-15")
		self.item_2 = Inventory.objects.create(owner=self.test_user, product_name="Safety Boots", price=65000, stock_level=20, date_added="2025-05-15")
		self.item_3 = Inventory.objects.create(owner=self.test_user, product_name="Helmet", price=6000, stock_level=45, date_added="2025-05-15")

		self.test_order = Order(product_owner_id=self.test_user, client_name="bob", client_email="bob@gmail.com", order_date="2025-07-20")
		self.ordered_product_1 = OrderedProduct(name="Calculator", quantity=1, price=10000)
		self.ordered_product_2 = OrderedProduct(name="Helmet", quantity=5, price=6000)
		self.test_order.ordered_products_objects = [self.ordered_product_1, self.ordered_product_2]
		self.test_order.save()


	def create_valid_new_order_req(self):
		data = {
			"client_name": "client1",
			"client_email": "clientemail@gmail.com",
			"client_phone": "08048672894",
			"order_date": "2025-07-20",
			"ordered_products": [
				{"name": "Helmet", "quantity": 40, "price": 6000},
				{"name": "calculator", "quantity": 10, "price": 10000} # test product name normalization
			]
		}

		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		response = self.client.post(reverse("orders", args=["v1"]), data, format="json")
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(response.data["detail"], "Order created successfully")
		new_order = Order.objects.get(pk=response.data["data"]["id"])
		self.assertEqual(340000, new_order.total_price)
		self.assertEqual(2, new_order.ordered_products.count())
		self.assertEqual("Helmet", new_order.ordered_products.all()[0].name)
		self.assertEqual("Calculator", new_order.ordered_products.all()[1].name)

	def create_order_req_with_incomplete_data(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		data = {
			"ordered_products": [
				{
					"quantity": 5.5,
					"price": 100,
				},
				{
					"name": "Helmet",
					"quantity": 0,
				},
				{
					"name": "Hen",
					"price": 5000
				},
			]
		}
		response = self.client.post(reverse("orders", args=["v1"]), data, format="json")

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertEqual(response.data["detail"]['client_name'][0], 'This field is required.')
		self.assertEqual(response.data["detail"]['order_date'][0], 'This field is required.')
		self.assertEqual(response.data["detail"]['ordered_products'][0]['name'][0], 'This field is required.')
		self.assertEqual(response.data["detail"]['ordered_products'][1]['price'][0], 'This field is required.')
		self.assertEqual(response.data["detail"]['ordered_products'][2]['quantity'][0], 'This field is required.')

	def create_order_req_with_invalid_date_added(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		data = {
			"client_name": "Mr. light bulb",
			"order_date": "2020-15-39",
			"ordered_products": [
				{
					"quantity": 5.5,
					"price": 100,
				}
			]
		}
		response = self.client.post(reverse("orders", args=["v1"]), data, format="json")
		self.assertEqual(response.data["detail"]['ordered_products'][0]['name'], ['This field is required.'])
		self.assertEqual(response.data["detail"]['ordered_products'][0]['quantity'], ['A valid integer is required.'])
		self.assertEqual(response.data["detail"]['order_date'], ['Date has wrong format. Use one of these formats instead: YYYY-MM-DD.'])
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

	def create_order_req_for_missing_inventory_item(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		data = {
			"client_name": "tyler",
			"client_email": "tylerdurden@gmail.com",
			"client_phone": "09018372693",
			"order_date": "2025-07-20",
			"ordered_products": [
				{
					"name": "Wisdom",
					"quantity": 40,
					"price": 6000,
				}
			]
		}

		response = self.client.post(reverse("orders", args=["v1"]), data, format="json")
		self.assertEqual(response.data["detail"]["ordered_products"], {"Wisdom": ["'Wisdom' doesn't exist in the Inventory."]})
		self.assertRaises(Order.DoesNotExist, Order.objects.get, client_name="tyler")
		
	def create_order_req_for_item_with_invalid_quantity_and_price(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		data = {
			"client_name": "person",
			"client_email": "person@gmail.com",
			"client_phone": "09018372693",
			"order_date": "2025-07-20",
			"ordered_products": [
				{
					"name": "Helmet",
					"quantity": 50,
					"price": 6300,
				}
			]
		}

		response = self.client.post(reverse("orders", args=["v1"]), data, format="json")
		self.assertEqual(response.data["detail"]["ordered_products"], {
			"Helmet": ["Not enough products in stock to satisfy order for 'Helmet'","Price isn't the same as that of inventory item for 'Helmet'"]
		})
		self.assertRaises(Order.DoesNotExist, Order.objects.get, client_name="person")

	def create_order_req_with_non_unique_ordered_product_data(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		data = {
			"client_name": "customer",
			"client_email": "customer@email.com",
			"order_date": "2025-07-20",
			"ordered_products": [
				{
					"name": "Safety Boots",
					"quantity": 1,
					"price": 65000,
				},
				{
					"name": "Safety Boots",
					"quantity": 2,
					"price": 65000,
				}
			]
		}
		response = self.client.post(reverse("orders", args=["v1"]), data, format="json")
		self.assertEqual(response.data["detail"]["ordered_products"], {
			"Safety Boots": ["Ordered products must be unique. Use the quantity field to specify multiple orders of same item."]
		})
		self.assertRaises(Order.DoesNotExist, Order.objects.get, client_name="customer")


	def test_create_order_reqs_with_credentials(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		self.create_order_req_with_incomplete_data()
		self.create_valid_new_order_req()
		self.create_order_req_with_non_unique_ordered_product_data()
		self.create_order_req_for_missing_inventory_item()
		self.create_order_req_with_invalid_date_added()

	def test_create_order_req_without_credentials(self):
		response = self.client.post(reverse("orders", args=["v1"]), {"product_name": "product-1", "stock_level": 5, "price": 800})
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_get_all_orders_with_credentials(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		response = self.client.get(reverse("orders", args=["v1"]))
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["data"]["page_count"], 1)
		self.assertEqual(response.data["data"]["next_page"], None)
		self.assertEqual(response.data["data"]["prev_page"], None)
		order_count = Order.objects.filter(product_owner_id=self.test_user.id).count()
		self.assertEqual(1, order_count)
		self.assertEqual(response.data["data"]["length"], order_count)
		self.assertEqual(response.data["data"]["orders"][0]["client_name"], "bob")
		self.assertEqual(response.data["data"]["orders"][0]["order_date"], "2025-07-20")

	def get_orders_by_status(self):
		response = self.client.get(reverse("orders", args=["v1"]), query_params={"status": "Delivered"}, format='json')
		self.assertEqual(response.data["data"]["length"], 2)
		self.assertEqual(response.data["data"]["orders"][0]["client_name"], "Batman") # Batman comes first because of the default ordering order
		self.assertEqual(response.data["data"]["orders"][1]["client_name"], "prismo")
		self.assertEqual(response.status_code, status.HTTP_200_OK)

		response = self.client.get(reverse("orders", args=["v1"]), query_params={"status": "Pending"}, format='json')
		self.assertEqual(response.data["data"]["length"], 2)
		self.assertEqual(response.data["data"]["orders"][0]["client_name"], "bob") # bob comes first because of the default ordering order
		self.assertEqual(response.data["data"]["orders"][1]["client_name"], "gumball")
		self.assertEqual(response.status_code, status.HTTP_200_OK)

	def get_orders_by_search(self):
		response = self.client.get(reverse("orders", args=["v1"]), query_params={"query": "bag"}, format='json')
		self.assertEqual(response.data["data"]["length"], 1)
		self.assertEqual(response.data["data"]["orders"][0]["client_name"], "prismo")
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		
		response = self.client.get(reverse("orders", args=["v1"]), query_params={"query": "Tape"}, format='json')
		self.assertEqual(response.data["data"]["length"], 1)
		self.assertEqual(response.data["data"]["orders"][0]["client_name"], "Batman")
		self.assertEqual(response.status_code, status.HTTP_200_OK)

	def get_orders_ordered_by_id(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		orderedItems = Order.objects.filter(product_owner_id=self.test_user).order_by("id")

		response = self.client.get(reverse("orders", args=["v1"]), query_params={"order": "id"}, format='json')
		self.assertEqual(response.data["data"]["length"], 4)
		self.assertEqual(response.data["data"]["orders"][0]["client_name"], orderedItems.first().client_name)
		self.assertEqual(response.data["data"]["orders"][3]["client_name"], orderedItems.last().client_name)
		self.assertEqual(response.status_code, status.HTTP_200_OK)

		response = self.client.get(reverse("orders", args=["v1"]), query_params={"order": "-id"}, format='json')
		self.assertEqual(response.data["data"]["length"], 4)
		self.assertEqual(response.data["data"]["orders"][0]["client_name"], orderedItems.last().client_name)
		self.assertEqual(response.data["data"]["orders"][3]["client_name"], orderedItems.first().client_name)
		self.assertEqual(response.status_code, status.HTTP_200_OK)

	def get_orders_ordered_by_order_date(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)

		response = self.client.get(reverse("orders", args=["v1"]), query_params={"order": "order_date"}, format='json')
		self.assertEqual(response.data["data"]["length"], 4)
		self.assertEqual(response.data["data"]["orders"][0]["client_name"], "prismo")
		self.assertEqual(response.data["data"]["orders"][3]["client_name"], "bob")
		self.assertEqual(response.status_code, status.HTTP_200_OK)

		response = self.client.get(reverse("orders", args=["v1"]), query_params={"order": "-order_date"}, format='json')
		self.assertEqual(response.data["data"]["length"], 4)
		self.assertEqual(response.data["data"]["orders"][0]["client_name"], "bob")
		self.assertEqual(response.data["data"]["orders"][3]["client_name"], "prismo")
		self.assertEqual(response.status_code, status.HTTP_200_OK)

	def get_orders_ordered_by_total_price(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		# 40k bob, 201k prismo, 9k gumball, 105k batman
		response = self.client.get(reverse("orders", args=["v1"]), query_params={"order": "total_price"}, format='json')

		self.assertEqual(response.data["data"]["length"], 4)
		self.assertEqual(response.data["data"]["orders"][0]["client_name"], "gumball")
		self.assertEqual(response.data["data"]["orders"][3]["client_name"], "prismo")
		self.assertEqual(response.status_code, status.HTTP_200_OK)

		response = self.client.get(reverse("orders", args=["v1"]), query_params={"order": "-total_price"}, format='json')
		self.assertEqual(response.data["data"]["length"], 4)
		self.assertEqual(response.data["data"]["orders"][0]["client_name"], "prismo")
		self.assertEqual(response.data["data"]["orders"][3]["client_name"], "gumball")
		self.assertEqual(response.status_code, status.HTTP_200_OK)

	def test_get_orders_with_credentials_and_query_params(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)

		item_1 = Inventory.objects.create(owner=self.test_user, product_name="Bag", price=16000, stock_level=75, date_added="2025-05-15")
		item_2 = Inventory.objects.create(owner=self.test_user, product_name="Tape", price=6000, stock_level=85, date_added="2025-05-15")
		item_3 = Inventory.objects.create(owner=self.test_user, product_name="Head Phones", price=9000, stock_level=100, date_added="2025-05-15")

		order_1 = Order(product_owner_id=self.test_user, client_name="prismo", client_email="prismo@gmail.com", status="Delivered", order_date="2025-07-15")
		order_2 = Order(product_owner_id=self.test_user, client_name="gumball", client_email="gumballwatterson@elmoremail.com", order_date="2025-07-16")
		order_3 = Order(product_owner_id=self.test_user, client_name="Batman", client_email="brucewayne@wayne.gotham", status="Delivered", order_date="2025-07-17")

		order_1.ordered_products_objects = [OrderedProduct(name="Bag", quantity=12, price=16000), OrderedProduct(name="Head Phones", quantity=1, price=9000)]
		order_1.save()
		order_2.ordered_products_objects = [OrderedProduct(name="Head Phones", quantity=1, price=9000)]
		order_2.save()
		order_3.ordered_products_objects = [OrderedProduct(name="Tape", quantity=10, price=6000), OrderedProduct(name="Head Phones", quantity=5, price=9000)]
		order_3.save()

		self.get_orders_by_status()
		self.get_orders_by_search()
		self.get_orders_ordered_by_id()
		self.get_orders_ordered_by_order_date()
		self.get_orders_ordered_by_total_price()
		
	def test_get_orders_without_credentials(self):
		response = self.client.get(reverse("orders", args=["v1"]))
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_get_single_order_with_credentials(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		response = self.client.get(reverse("order", args=["v1", str(self.test_order.id)]), format="json")
		expected_data = OrderSerializer(self.test_order).data
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["data"], expected_data)

		response = self.client.get(reverse("order", args=["v1", '99999999999']), format="json")
		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
		self.assertEqual(response.data["detail"], "Order not found")

	def test_get_single_order_without_credentials(self):
		response = self.client.get(reverse("order", args=["v1", "1"]), format="json")
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_update_order_with_valid_data(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		order = Order(product_owner_id=self.test_user, client_name="Tim", client_email="timilehin@tmail.com", order_date="2025-03-2")
		ordered_product_1 = OrderedProduct(name="Safety Boots", quantity=1, price=65000)
		ordered_product_2 = OrderedProduct(name="Helmet", quantity=5, price=6000)
		order.ordered_products_objects = [ordered_product_1, ordered_product_2]
		order.save()

		self.assertEqual(order.client_name, "Tim")
		self.assertRegex(order.order_date, "2025-03-2")
		self.assertEqual(order.delivery_date, None)

		update_payload = {
			"client_name": "sam",
			"client_email": "sam45@gmail.com",
			"client_phone": "07014537372",
			"status": "Delivered",
			"order_date": "2025-4-8"
		}

		response = self.client.put(reverse("order", args=["v1", str(order.id)]), update_payload, format="json")
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		order = Order.objects.get(pk=order.id)
		self.assertEqual(order.client_name, "sam")
		self.assertEqual(order.client_email, "sam45@gmail.com")
		self.assertEqual(order.client_phone, "07014537372")
		self.assertEqual(order.status, "Delivered")
		self.assertEqual(order.order_date, date.fromisoformat("2025-04-08"))
		self.assertRegex(order.delivery_date.isoformat(), r'^\d{4}-\d{2}-\d{2}')


	def test_delete_order_with_credentials(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)

		order_to_delete = Order(product_owner_id=self.test_user, client_name="Damola", order_date="2025-06-02")
		ordered_product = OrderedProduct(name="Safety Boots", quantity=1, price=65000)
		order_to_delete.ordered_products_objects = [ordered_product]
		order_to_delete.save()

		response = self.client.delete(reverse("order", args=["v1", str(order_to_delete.id)]), format="json")
		self.assertRaises(Order.DoesNotExist, Order.objects.get, pk=self.item_3.id)
		self.assertEqual(response.data["detail"], "Order deleted successfully")
		self.assertEqual(response.status_code, status.HTTP_200_OK)

		response = self.client.delete(reverse("order", args=["v1", "999999999"]), format="json")
		self.assertEqual(response.data["detail"], "Order not found")
		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

	def test_delete_order_without_credentials(self):
		response = self.client.delete(reverse("order", args=["v1", '3']), format="json")
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_get_order_stats(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		new_order = Order(product_owner_id=self.test_user, client_name="bmo", client_email="bmo@nomail.com", status="Delivered", order_date="2025-04-15")
		new_order.ordered_products_objects = [OrderedProduct(name="Calculator", quantity=1, price=10000)]
		new_order.save()

		response = self.client.get(reverse("orders-stats", args=["v1"]), format="json")
		self.assertEqual(response.data["data"]["total_orders"], 2)
		self.assertEqual(response.data["data"]["total_revenue"], 50000)
		self.assertEqual(response.data["data"]["pending_orders"], 1)
		self.assertEqual(response.status_code, status.HTTP_200_OK)

class OrderedProductViewTest(APITransactionTestCase):
	def setUp(self):
		self.user = CustomUser.objects.create(
			business_name="All-biz", full_name="larry", email="larry123@gmail.com", password="12345678", is_active=True
		)
		self.refresh_obj = RefreshToken.for_user(self.user)
		self.access_token = str(self.refresh_obj.access_token)

		self.item = Inventory.objects.create(owner=self.user, product_name="Cup", price=800, stock_level=100, date_added="2025-05-15")

		self.order = Order(product_owner_id=self.user, client_name="bob", client_email="bob@gmail.com", order_date="2025-04-15")
		self.ordered_product = OrderedProduct(name="Cup", quantity=5, price=800)
		self.order.ordered_products_objects = [self.ordered_product]
		self.order.save()

	def test_add_new_ordered_product_to_order(self):
		Inventory.objects.create(owner=self.user, product_name="Plate", price=1500, stock_level=100, date_added="2025-05-15")

		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		data = {"name": "Plate", "quantity": 2, "price": 1500}
		response = self.client.post(reverse("ordered-products", args=["v1", str(self.order.id)]), data, format="json")

		self.assertEqual(response.data["detail"], "product added to Order successfully")
		self.assertEqual(OrderedProduct.objects.get(name="Plate").price, 1500)
		self.assertEqual(Order.objects.get(pk=self.order.id).total_price, 7000)
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		

	def test_get_ordered_product_without_credentials(self):
		response = self.client.delete(reverse("ordered-product", args=["v1", str(self.order.id), str(self.ordered_product.id)]), format="json")
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_get_existing_ordered_product_by_id(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)

		response = self.client.get(reverse("ordered-product", args=["v1", str(self.order.id), str(self.ordered_product.id)]), format="json")
		self.assertEqual(response.data["data"]["name"], "Cup")
		self.assertEqual(response.data["data"]["price"], "800.00") # why is it serialized as a string tho?
		self.assertEqual(response.data["data"]["quantity"], 5)
		self.assertEqual(response.status_code, status.HTTP_200_OK)

	def test_get_nonexistent_ordered_product_by_id(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)

		response = self.client.get(reverse("ordered-product", args=["v1", "99999999", str(self.ordered_product.id)]), format="json")
		self.assertEqual(response.data["detail"], "Order not found")
		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

		response = self.client.get(reverse("ordered-product", args=["v1", str(self.order.id), "99999999"]), format="json")
		self.assertEqual(response.data["detail"], "Ordered Product not found")
		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

	def test_update_ordered_product_quantity(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)

		order = Order.objects.get(pk=self.order.id)
		self.assertEqual(order.total_price, 4000)

		response = self.client.put(reverse("ordered-product", args=["v1", str(self.order.id), str(self.ordered_product.id)]), {"quantity": 2}, format="json")
		self.assertEqual(OrderedProduct.objects.get(pk=self.ordered_product.id).quantity, 2)
		order = Order.objects.get(pk=self.order.id)
		self.assertEqual(order.total_price, 1600)
		self.assertEqual(response.status_code, status.HTTP_200_OK)

	def test_update_ordered_product_without_credentials(self):
		response = self.client.put(reverse("ordered-product", args=["v1", str(self.order.id), str(self.ordered_product.id)]), format="json")
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_update_ordered_product_price(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)

		order = Order.objects.get(pk=self.order.id)
		self.assertEqual(order.total_price, 4000)

		response = self.client.put(reverse("ordered-product", args=["v1", str(self.order.id), str(self.ordered_product.id)]), {"price": 2000}, format="json")
		self.assertEqual(OrderedProduct.objects.get(pk=self.ordered_product.id).price, 800)
		order = Order.objects.get(pk=self.order.id)
		self.assertEqual(order.total_price, 4000)
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

	def test_delete_ordered_product_without_credentials(self):
		response = self.client.delete(reverse("ordered-product", args=["v1", str(self.order.id), str(self.ordered_product.id)]), format="json")
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_delete_ordered_product_ok(self):
		Inventory.objects.create(owner=self.user, product_name="Plate", price=1500, stock_level=100, date_added="2025-05-15")
		new_ordered_product = OrderedProduct(name="Plate", quantity=2, price=1500, order_id=self.order)
		new_ordered_product.save(new_order=False)

		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		
		response = self.client.delete(reverse("ordered-product", args=["v1", str(self.order.id), str(self.ordered_product.id)]), format="json")
		self.assertRaises(OrderedProduct.DoesNotExist, OrderedProduct.objects.get, pk=self.ordered_product.id)
		self.assertEqual(response.data["detail"], "Ordered product deleted successfully")
		self.assertEqual(response.status_code, status.HTTP_200_OK)

	def test_delete_only_ordered_product(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		
		response = self.client.delete(reverse("ordered-product", args=["v1", str(self.order.id), str(self.ordered_product.id)]), format="json")
		self.assertEqual(response.data["detail"], "The only ordered product of an order can't be deleted. An Order must have at least one ordered product")
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

	def test_delete_ordered_product_of_delivered_order(self):
		self.order.status = "Delivered"
		self.order.save()

		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		
		response = self.client.delete(reverse("ordered-product", args=["v1", str(self.order.id), str(self.ordered_product.id)]), format="json")
		self.assertEqual(response.data["detail"], "Only the Ordered products of Pending Orders can be deleted")
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
