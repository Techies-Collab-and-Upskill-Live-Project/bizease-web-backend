from rest_framework.test import APITransactionTestCase
from django.test import TestCase
from .models import Order, OrderedProduct
from .serializers import OrderedProductSerializer, OrderSerializer
from accounts.models import CustomUser
from inventory.models import Inventory
from django.db.utils import IntegrityError
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken


class OrderModelTest(TestCase):
	@classmethod
	def setUp(cls):
		cls.test_user = CustomUser.objects.create(business_name="Business 3", full_name="Business Man 3", email="businessman3@gmail.com", password="12345678")
		cls.product_1 = Inventory.objects.create(owner=cls.test_user, product_name="A3 Paper", price=50, stock_level=500)
		cls.product_2 = Inventory.objects.create(owner=cls.test_user, product_name="Satchet Water", price=30, stock_level=300)
		cls.product_3 = Inventory.objects.create(owner=cls.test_user, product_name="Sneakers", price=25000, stock_level=150)

		cls.order = Order(product_owner_id=cls.test_user, client_name="naive client", client_email="n_client@gmail.com", client_phone="09012367903", )
		cls.item = OrderedProduct(name="Sneakers", quantity=2, price=25000)
		cls.order.ordered_products_objects = [cls.item]
		cls.order.save()

		cls.order_1 = Order(product_owner_id=cls.test_user, client_name="person", client_email="person@gmail.com", client_phone="09012367903", )
		cls.item_1 = OrderedProduct(name="Satchet Water", quantity=20, price=30)
		cls.item_2 = OrderedProduct(name="A3 Paper", quantity=2, price=50)
		cls.order_1.ordered_products_objects = [cls.item_1, cls.item_2]
		cls.order_1.save()
		# test max_length is enforced

	def test_save_new_order_instance(self):
		order_1 = Order(product_owner_id=self.test_user, client_name="customer1", client_email="customer1@gmail.com", client_phone="08149672890")
		self.assertRaises(ValueError, order_1.save)
		ordered_product_1 = OrderedProduct(name="Satchet Water", quantity=4, price=30)
		ordered_product_2 = OrderedProduct(name="A3 Paper", quantity=4, price=50)
		order_1.ordered_products_objects = [ordered_product_1, ordered_product_2]
		order_1.save()
		order_1 = Order.objects.get(pk=order_1.id)
		self.assertEqual(order_1.client_name, "customer1")
		self.assertEqual(order_1.client_email, "customer1@gmail.com")
		self.assertEqual(order_1.client_phone, "08149672890")
		self.assertEqual(order_1.status, "Pending")
		self.assertEqual(order_1.total_price, 320)
		self.assertRegex(order_1.order_date.isoformat().replace('+00:00', 'Z'), r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{6}Z$')
		self.assertEqual(order_1.delivery_date, None)
		self.assertEqual(order_1.ordered_products.count(), 2)
		ordered_items = order_1.ordered_products.all().order_by("id")
		self.assertEqual(ordered_items[0].name, "Satchet Water")
		self.assertEqual(ordered_items[1].name, "A3 Paper")

	def test_save_new_order_with_invalid_ordered_item(self):
		order = Order(product_owner_id=self.test_user, client_name="customer1", client_email="customer1@gmail.com", client_phone="08149672890")
		ordered_product = OrderedProduct(name="Invalid item", quantity=4, price=30)
		order.ordered_products_objects = [ordered_product]
		self.assertEqual(order.save(), {"Invalid Item": ["'Invalid Item' doesn't exist in the Inventory."]})

		order = Order(product_owner_id=self.test_user, client_name="customer1", client_email="customer1@gmail.com", client_phone="08149672890")
		ordered_product = OrderedProduct(name="Satchet Water", quantity=501, price=20)
		order.ordered_products_objects = [ordered_product]
		self.assertEqual(order.save(), {
			"Satchet Water": [
				"Not enough products in stock to satisfy order for 'Satchet Water'",
				"Price isn't the same as that of inventory item for 'Satchet Water'"
			]
		})

	def test_add_new_valid_product_to_order(self):
		order = Order(product_owner_id=self.test_user, client_name="customer3", client_email="customer3@gmail.com", client_phone="07146372890", )
		order.ordered_products_objects = [OrderedProduct(name="Sneakers", quantity=2, price=25000)]
		order.save()
		self.assertEqual(Order.objects.get(pk=order.id).total_price, 50000)

		new_ordered_product = OrderedProduct(name="A3 Paper", quantity=5, price=50, order_id=order)
		new_ordered_product.save(new_order=False)
		self.assertEqual(Inventory.objects.get(pk=self.product_3.id).stock_level, 146) # sneakers
		self.assertEqual(Inventory.objects.get(pk=self.product_1.id).stock_level, 493) # A3 Paper
		self.assertEqual(Order.objects.get(pk=order.id).total_price, 50250)
		# Order.ordered_products.add(ordered_product)

	def test_add_constraint_violating_product_to_order(self):
		order = Order(product_owner_id=self.test_user, client_name="customer2", client_email="customer2@gmail.com", client_phone="08146272890")
		ordered_product_1 = OrderedProduct(name="Satchet Water", quantity=5, price=30)
		order.ordered_products_objects = [ordered_product_1]
		order.save()
		ordered_product_2 = OrderedProduct(name="Satchet Water", order_id=order, quantity=1, price=30)
		self.assertRaises(IntegrityError, ordered_product_2.save)

	def test_non_updatable_fields(self):
		self.item_1.order_id = self.order
		self.assertRaises(ValueError, self.item_1.save)

		self.item_1.name = "A3 Paper"
		self.item_1.price = 50
		self.assertRaises(ValueError, self.item_1.save)

		self.item_1.cummulative_price = 2000
		self.assertRaises(ValueError, self.item_1.save)

	def test_update_ordered_product_quantity(self):
		self.assertEqual(self.order_1.total_price, 700)
		self.item_2.quantity = 30
		self.item_2.save()

		self.assertEqual(self.item_2.quantity, 30)
		self.assertEqual(self.order_1.total_price, 2100)
		self.assertEqual(Inventory.objects.get(pk=self.product_1.id).stock_level, 470)


class OrderedProductModelTest(TestCase):
	# data_validation, constraints, max_length e.t.c.

	@classmethod
	def setUp(cls):
		cls.test_user = CustomUser.objects.create(business_name="melon inc.", full_name="Melon Tusk", email="melontusk@gmail.com", password="12345678")
		cls.product_1 = Inventory.objects.create(owner=cls.test_user, product_name="Water Melon", price=1500, stock_level=200)
		cls.product_2 = Inventory.objects.create(owner=cls.test_user, product_name="Winter Melon", price=2000, stock_level=200)
		cls.product_3 = Inventory.objects.create(owner=cls.test_user, product_name="Cantaloupe", price=1000, stock_level=200)

		cls.test_order = Order(product_owner_id=cls.test_user, client_name="melon-client")
		cls.item = OrderedProduct(name="Water Melon", quantity=2, price=1500)
		cls.test_order.ordered_products_objects = [cls.item]
		cls.test_order.save()

	def test_create_valid_ordered_product(self):
		new_ordered_item = OrderedProduct(name="Cantaloupe", quantity=4, price=1000)
		new_ordered_item.order_id = self.test_order
		new_ordered_item.save(new_order=False)

		new_ordered_item = OrderedProduct.objects.get(pk=new_ordered_item.id)
		test_order = Order.objects.get(pk=self.test_order.id)
		self.assertEqual(test_order.total_price, 7000)
		self.assertEqual(new_ordered_item.order_id.id, test_order.id)
		self.assertEqual(Inventory.objects.get(product_name="Cantaloupe").stock_level, 196)

	def test_create_invalid_ordered_product(self):
		new_order = Order(product_owner_id=self.test_user, client_name="bob")
		new_order.ordered_products_objects = [OrderedProduct(name="Winter Melon", quantity=4, price=2000)]
		new_order.save()

		item = OrderedProduct(name="Cantaloupe", quantity=204, price=1200)
		item_1 = OrderedProduct(name="Bitter Melon", quantity=4, price=1000)
		item.order_id = new_order
		item_1.order_id = new_order

		errors_1 = item.save()
		expected_errs = ["Not enough products in stock to satisfy order for 'Cantaloupe'", "Price isn't the same as that of inventory item for 'Cantaloupe'"]
		self.assertEqual(errors_1, expected_errs)
		self.assertEqual(item_1.save(), ["'Bitter Melon' doesn't exist in the Inventory."])

	def test_updating_quantity_field(self):
		existing_ordered_item = OrderedProduct.objects.get(pk=self.item.id)
		existing_ordered_item.quantity = 10
		existing_ordered_item.save(new_order=False)

		existing_ordered_item = OrderedProduct.objects.get(pk=self.item.id)
		self.assertEqual(existing_ordered_item.quantity, 10)
		self.assertEqual(existing_ordered_item.cummulative_price, 15000)
		self.test_order = Order.objects.get(pk=self.test_order.id)
		self.assertEqual(self.test_order.total_price, 15000)

		existing_ordered_item.quantity = 10000
		errors = existing_ordered_item.save()
		self.assertEqual(errors, [f"Not enough products in stock to satisfy order for '{existing_ordered_item.name}'"])

	def test_updating_other_fields(self):
		existing_ordered_item = OrderedProduct.objects.get(pk=self.item.id)

		existing_ordered_item.order_id = Order(product_owner_id=self.test_user, client_name="Ace")
		self.assertRaises(ValueError, existing_ordered_item.save)
		existing_ordered_item.cummulative_price = 3
		self.assertRaises(ValueError, existing_ordered_item.save)


	def test_delete_only_ordered_item_of_order(self):
		self.assertRaises(ValueError, OrderedProduct.objects.get(pk=self.item.id).delete)

	def test_valid_ordered_item_delete(self):
		new_order = Order(product_owner_id=self.test_user, client_name="bob")
		item_to_delete = OrderedProduct(name="Winter Melon", quantity=2, price=2000)
		new_order.ordered_products_objects = [OrderedProduct(name="Cantaloupe", quantity=4, price=1000), item_to_delete]
		new_order.save()

		self.assertEqual(new_order.total_price, 8000)
		self.assertEqual(Inventory.objects.get(product_name="Winter Melon").stock_level, 198)

		target_id = item_to_delete.id
		item_to_delete.delete()
		self.assertRaises(OrderedProduct.DoesNotExist, OrderedProduct.objects.get, pk=target_id)
		new_order = Order.objects.get(pk=new_order.id)
		self.assertEqual(new_order.total_price, 4000)
		self.assertEqual(Inventory.objects.get(product_name="Winter Melon").stock_level, 200)

	def test_delete_ordered_item_out_of_stock(self):
		product = Inventory.objects.create(owner=self.test_user, product_name="Snap Melon", price=500, stock_level=100)
		new_order = Order(product_owner_id=self.test_user, client_name="Marla")
		item_to_delete = OrderedProduct(name="Snap Melon", quantity=10, price=500)
		new_order.ordered_products_objects = [OrderedProduct(name="Cantaloupe", quantity=4, price=1000), item_to_delete]
		new_order.save()
		product.delete()
		self.assertEqual(new_order.total_price, 9000)

		target_id = item_to_delete.id
		item_to_delete.delete()
		self.assertRaises(OrderedProduct.DoesNotExist, OrderedProduct.objects.get, pk=target_id)
		new_order = Order.objects.get(pk=new_order.id)
		self.assertEqual(new_order.total_price, 4000)
	

class OrderSerializersTest(TestCase):
	@classmethod
	def setUp(cls):
		cls.test_user = CustomUser.objects.create(
			business_name="Business 2", full_name="Business Man 2", email="businessman2@email.com", password="12345678"
		)
		cls.product_1 = Inventory.objects.create(owner=cls.test_user, product_name="Bread", price=500, stock_level=50)
		cls.product_3 = Inventory.objects.create(owner=cls.test_user, product_name="Pen", price=100, stock_level=105)
		cls.product_4 = Inventory.objects.create(owner=cls.test_user, product_name="Detergent", price=800, stock_level=75)

		cls.test_order = Order(product_owner_id=cls.test_user, client_name="client1", client_email="clientemail@gmail.com", client_phone="08048672894")
		cls.ordered_product_1 = OrderedProduct(name="Pen", quantity=40, price=100)
		cls.ordered_product_2 = OrderedProduct(name="Bread", quantity=6, price=500)
		cls.ordered_product_3 = OrderedProduct(name="Detergent", quantity=3, price=800)
		cls.test_order.ordered_products_objects = [cls.ordered_product_1, cls.ordered_product_2, cls.ordered_product_3]
		cls.test_order.save()

	def test_order_serialization(self):
		expected_output = {
			"id": self.test_order.id,
			"status": "Pending",
			"client_name": "client1",
			"client_email": "clientemail@gmail.com",
			"client_phone": "08048672894",
			"order_date": self.test_order.order_date.isoformat().replace('+00:00', 'Z'),
			"delivery_date": None,
			"total_price": 9400,
			"ordered_products": [
				{
					"id": self.ordered_product_1.id,
					"name": "Pen",
					"quantity": 40,
					"price": "100.00",
					"cummulative_price": "4000.00"
				},
				{
					"id": self.ordered_product_2.id,
					"name": "Bread",
					"quantity": 6,
					"price": "500.00",
					"cummulative_price": "3000.00"
				},
				{
					"id": self.ordered_product_3.id,
					"name": "Detergent",
					"quantity": 3,
					"price": "800.00",
					"cummulative_price": "2400.00"
				},
			]
		}
		self.assertEqual(OrderSerializer(self.test_order).data, expected_output)

	# todo create Order with invalid data
	# Make sure the fields that are expected to be ignored are actually ignored
	def test_create_new_order(self):
		data = {
			"client_name": "good_customer",
			"client_email": "good_customer@gmail.com",
			"client_phone": "08134287605",
			"ordered_products": [
				{
					"name": "Pen",
					"quantity": 10,
					"price": 100,
				},
				{
					"name": "Bread",
					"quantity": 1,
					"price": 500,
				},
			]
		}

		serializer = OrderSerializer(data=data)
		if serializer.is_valid():
			new_order = serializer.save(self.test_user)["data"]

		# The model instance is re-fetched from the db to confirm the field values have 
		# actually been the saved to the db. They are not just attributes on this instance
		new_order = Order.objects.get(pk=new_order.id)

		self.assertEqual(new_order.client_name, "good_customer")
		self.assertEqual(new_order.client_email, "good_customer@gmail.com")
		self.assertEqual(new_order.client_phone, "08134287605")
		self.assertEqual(new_order.status, "Pending")
		self.assertEqual(new_order.total_price, 1500)
		self.assertRegex(new_order.order_date.isoformat().replace('+00:00', 'Z'), r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{6}Z$')
		self.assertEqual(new_order.delivery_date, None)
		self.assertEqual(new_order.ordered_products.count(), 2)
		ordered_items = new_order.ordered_products.all()
		self.assertEqual(ordered_items[0].name, "Pen")
		self.assertEqual(ordered_items[1].name, "Bread")

	def test_create_new_order_with_invalid_fields(self): # field level validation
		data = {
			"ordered_products": [
				{	
					"quantity": 5.5,
					"price": 100,
				},
				{
					"name": "Bread",
					"quantity": 1,
				},
				{
					"name": "Hen",
					"price": 5000
				},
				{
					"name": "",
					"price": "50", # todo: Make sure this string is marked as invalid
					"quantity": 0
				},
			]
		}

		serializer = OrderSerializer(data=data)
		self.assertEqual(serializer.is_valid(), False)

		self.assertEqual(str(serializer.errors['client_name'][0]), 'This field is required.')
		self.assertEqual(str(serializer.errors['ordered_products'][0]['name'][0]), 'This field is required.')
		self.assertEqual(str(serializer.errors['ordered_products'][1]['price'][0]), 'This field is required.')
		self.assertEqual(str(serializer.errors['ordered_products'][2]['quantity'][0]), 'This field is required.')

		self.assertEqual(str(serializer.errors['ordered_products'][3]['name'][0]), 'This field may not be blank.')
		# self.assertEqual(str(serializer.errors['ordered_products'][3]['price'][0]), 'Value must be a float or an integer')
		self.assertEqual(str(serializer.errors['ordered_products'][3]['quantity'][0]), 'Ensure this value is greater than or equal to 1.')

	def test_update_order(self):
		data = {
			"client_name": "client_1",
			"client_email": "client_1@gmail.com",
			"client_phone": "07048673894",
			"status": "Delivered"
		}

		serializer = OrderSerializer(self.test_order, data=data, partial=True)
		if serializer.is_valid():
			updated_order = serializer.save(self.test_user)["data"]

		# The model instance is re-fetched from the db to confirm the field values have 
		# actually been the saved to the db. Making sure they are not just attributes on this instance
		updated_order = Order.objects.get(pk=updated_order.id)

		self.assertEqual(updated_order.client_name, "client_1")
		self.assertEqual(updated_order.client_email, "client_1@gmail.com")
		self.assertEqual(updated_order.client_phone, "07048673894")
		self.assertEqual(updated_order.status, "Delivered")
		self.assertEqual(updated_order.total_price, 9400)
		self.assertRegex(updated_order.order_date.isoformat().replace('+00:00', 'Z'), r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{6}Z$')
		self.assertRegex(updated_order.delivery_date.isoformat().replace('+00:00', 'Z'), r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{6}Z$')
		self.assertEqual(updated_order.ordered_products.count(), 3)


class OrdersViewsTest(APITransactionTestCase):
	def setUp(self):
		self.test_user = CustomUser.objects.create(
			business_name="user-biz", full_name="test user", email="testuser123@gmail.com", password="12345678"
		)
		self.test_user_2 = CustomUser.objects.create(
			business_name="rocket-biz", full_name="rocket monkey", email="rocketmonkey@gmail.com", password="12345678"
		)
		self.refresh_obj = RefreshToken.for_user(self.test_user)
		# refresh_token = str(refresh_obj)
		self.access_token = str(self.refresh_obj.access_token)

		self.item_1 = Inventory.objects.create(owner=self.test_user, product_name="Calculator", price=10000, stock_level=100)
		self.item_2 = Inventory.objects.create(owner=self.test_user, product_name="Safety Boots", price=65000, stock_level=20)
		self.item_3 = Inventory.objects.create(owner=self.test_user, product_name="Helmet", price=6000, stock_level=45)

		self.test_order = Order(product_owner_id=self.test_user, client_name="bob", client_email="bob@gmail.com")
		self.ordered_product_1 = OrderedProduct(name="Calculator", quantity=1, price=10000)
		self.ordered_product_2 = OrderedProduct(name="Helmet", quantity=5, price=6000)
		self.test_order.ordered_products_objects = [self.ordered_product_1, self.ordered_product_2]
		self.test_order.save()


	def create_valid_new_order_req(self):
		data = {
			"client_name": "client1",
			"client_email": "clientemail@gmail.com",
			"client_phone": "08048672894",
			"ordered_products": [
				{"name": "Helmet", "quantity": 40, "price": 6000},
				{"name": "calculator", "quantity": 10, "price": 10000} # test product name normalization
			]
		}

		response = self.client.post(reverse("orders", args=["v1"]), data)
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(response.data["detail"], "Order created successfully")
		new_order = Order.objects.get(pk=response.data["data"]["id"])
		self.assertEqual(340000, new_order.total_price)
		self.assertEqual(2, new_order.ordered_products.count())
		self.assertEqual("Helmet", new_order.ordered_products.all()[0].name)
		self.assertEqual("Calculator", new_order.ordered_products.all()[1].name)

	def create_order_req_with_incomplete_data(self):
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
		response = self.client.post(reverse("orders", args=["v1"]), data)

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertEqual(response.data["detail"]['client_name'][0], 'This field is required.')
		self.assertEqual(response.data["detail"]['ordered_products'][0]['name'][0], 'This field is required.')
		self.assertEqual(response.data["detail"]['ordered_products'][1]['price'][0], 'This field is required.')
		self.assertEqual(response.data["detail"]['ordered_products'][2]['quantity'][0], 'This field is required.')

	def create_order_req_for_missing_inventory_item(self):
		data = {
			"client_name": "person",
			"client_email": "person@gmail.com",
			"client_phone": "09018372693",
			"ordered_products": [
				{
					"name": "Wisdom",
					"quantity": 40,
					"price": 6000,
				},
				{
					"name": "calculator",
					"quantity": 10,
					"price": 10000,
				},
				{
					"name": "Helmet",
					"quantity": 50,
					"price": 6300,
				}
			]
		}

		response = self.client.post(reverse("orders", args=["v1"]), data)
		self.assertEqual(response.data["detail"], {"Wisdom": ["'Wisdom' doesn't exist in the Inventory"]})
		err_obj = {
			"Wisdom": [
				"'Wisdom' doesn't exist in the Inventory",
				"Ordered products must be unique. Use the quantity field to specify multiple orders of same item."
			],
			"Calculator": ["Price isn't the same as that of inventory item for 'Calculator'"],
			"Helmet": [
				"Price isn't the same as that of inventory item for 'Helmet'",
				"Not enough products in stock to satisfy order for 'Helmet'"
			],
		}
		response = self.client.post(reverse("orders", args=["v1"]), data)
		self.assertEqual(response.data["detail"], err_obj)
		self.assertRaises(Order.DoesNotExist, Order.objects.get, client_name="person")

		
	def create_order_req_with_non_unique_ordered_product_data(self):
		print("==>", Inventory.objects.get(product_name="Helmet").stock_level)
		data = {
			"client_name": "customer",
			"client_email": "customer@email.com",
			"ordered_products": [
				{
					"name": "Helmet",
					"quantity": 1,
					"price": 6000,
				},
				{
					"name": "Helmet",
					"quantity": 10,
					"price": 6000,
				}
			]
		}
		response = self.client.post(reverse("orders", args=["v1"]), data)
		self.assertEqual(response.data["detail"], {
			"Helmet": ["Ordered products must be unique. Use the quantity field to specify multiple orders of same item."]
		})
		self.assertRaises(Order.DoesNotExist, Order.objects.get, client_name="customer")


	def test_create_order_reqs_with_credentials(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		self.create_order_req_with_incomplete_data()
		# self.create_valid_new_order_req()
		self.create_order_req_with_non_unique_ordered_product_data()
		# self.create_order_req_for_missing_inventory_item()

	def test_create_order_req_without_credentials(self):
		response = self.client.post(reverse("orders", args=["v1"]), {"product_name": "product-1", "stock_level": 5, "price": 800})
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def get_orders_data_filter_status_req_(self):
		pass
	def get_orders_paginated_data_req(self):
		pass
	def get_orders_search_req(self):
		pass
	def get_orders_req_for_ordered_data(self):
		pass

	def test_get_orders_with_credentials(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		response = self.client.get(reverse("orders", args=["v1"]))
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["data"]["page_count"], 1)
		self.assertEqual(response.data["data"]["next_page"], None)
		self.assertEqual(response.data["data"]["prev_page"], None)
		order_count = Order.objects.filter(product_owner_id=self.test_user.id).count()
		self.assertEqual(1, order_count)
		self.assertEqual(response.data["data"]["length"], order_count)
		# Test the products returned but it seems like we need to set default ordering first
		# Test the query params firsts

	def test_get_orders_without_credentials(self):
		response = self.client.get(reverse("orders", args=["v1"]))
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_get_single_order_with_credentials(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		response = self.client.get(reverse("order", args=["v1", str(self.test_order.id)]))
		expected_data = OrderSerializer(self.test_order).data
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["data"], expected_data)

		response = self.client.get(reverse("order", args=["v1", '99999999999']))
		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
		self.assertEqual(response.data["detail"], "Order not found")

	def test_get_single_inventory_item_without_credentials(self):
		response = self.client.get(reverse("order", args=["v1", "1"]))
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def update_order_with_valid_data(self):
		order = Order(product_owner_id=self.test_user, client_name="Tim", client_email="timilehin@tmail.com")
		ordered_product_1 = OrderedProduct(name="Safety Boots", quantity=1, price=65000)
		ordered_product_2 = OrderedProduct(name="Helmet", quantity=5, price=6000)
		order.ordered_products_objects = [ordered_product_1, ordered_product_2]
		order.save()

		self.assertEqual(order.client_name, "Tim")
		self.assertRegex(order.order_date.isoformat().replace('+00:00', 'Z'), r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{6}Z$')
		self.assertEqual(order.delivery_date, None)

		update_payload = {
			"client_name": "sam",
			"client_email": "sam45@gmail.com",
			"client_phone": "07014537372",
			"status": "Delivered"
		}

		response = self.client.put(reverse("order", args=["v1", str(order.id)]), update_payload)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		order = Order.objects.get(pk=order.id)
		self.assertEqual(order.client_name, "sam")
		self.assertEqual(order.client_email, "sam45@gmail.com")
		self.assertEqual(order.client_phone, "07014537372")
		self.assertRegex(order.status, "Delivered")
		self.assertRegex(order.delivery_date.isoformat().replace('+00:00', 'Z'), r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{6}Z$')

	def test_update_single_inventory_item_with_credentials(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
		self.update_order_with_valid_data()
		# self.update_item_with_invalid_data

	def test_delete_order_with_credentials(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)

		order_to_delete = Order(product_owner_id=self.test_user, client_name="Damola")
		ordered_product = OrderedProduct(name="Safety Boots", quantity=1, price=65000)
		order_to_delete.ordered_products_objects = [ordered_product]
		order_to_delete.save()

		response = self.client.delete(reverse("order", args=["v1", str(order_to_delete.id)]))
		self.assertRaises(Order.DoesNotExist, Order.objects.get, pk=self.item_3.id)
		self.assertEqual(response.data["detail"], "Order deleted successfully")
		self.assertEqual(response.status_code, status.HTTP_200_OK)

		response = self.client.delete(reverse("order", args=["v1", "999999999"]))
		self.assertEqual(response.data["detail"], "Order not found")
		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

	def test_delete_order_without_credentials(self):
		response = self.client.delete(reverse("order", args=["v1", '3']))
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)