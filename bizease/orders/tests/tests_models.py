from django.test import TestCase
from orders.models import Order, OrderedProduct
from accounts.models import CustomUser
from inventory.models import Inventory
from django.db.utils import IntegrityError
from datetime import date


class OrderModelTest(TestCase):
	@classmethod
	def setUp(cls):
		cls.test_user = CustomUser.objects.create(business_name="Business 3", full_name="Business Man 3", email="businessman3@gmail.com", password="12345678")
		cls.product_1 = Inventory.objects.create(owner=cls.test_user, product_name="A3 Paper", price=50, stock_level=500, date_added="2025-03-15")
		cls.product_2 = Inventory.objects.create(owner=cls.test_user, product_name="Satchet Water", price=30, stock_level=300, date_added="2025-04-15")
		cls.product_3 = Inventory.objects.create(owner=cls.test_user, product_name="Sneakers", price=25000, stock_level=150, date_added="2025-05-15")

		cls.order = Order(product_owner_id=cls.test_user, client_name="naive client", client_email="n_client@gmail.com", client_phone="09012367903", order_date="2025-07-20")
		cls.item = OrderedProduct(name="Sneakers", quantity=2, price=25000)
		cls.order.ordered_products_objects = [cls.item]
		cls.order.save()

		cls.order_1 = Order(product_owner_id=cls.test_user, client_name="person", client_email="person@gmail.com", client_phone="09012367903", order_date="2025-07-20")
		cls.item_1 = OrderedProduct(name="Satchet Water", quantity=20, price=30)
		cls.item_2 = OrderedProduct(name="A3 Paper", quantity=2, price=50)
		cls.order_1.ordered_products_objects = [cls.item_1, cls.item_2]
		cls.order_1.save()
		# test max_length is enforced

	def test_save_new_order_instance(self):
		order_1 = Order(product_owner_id=self.test_user, client_name="customer1", client_email="customer1@gmail.com", client_phone="08149672890", order_date="2025-07-20")
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
		self.assertEqual(order_1.order_date, date.fromisoformat("2025-07-20"))
		self.assertEqual(order_1.delivery_date, None)
		self.assertEqual(order_1.ordered_products.count(), 2)
		ordered_items = order_1.ordered_products.all().order_by("id")
		self.assertEqual(ordered_items[0].name, "Satchet Water")
		self.assertEqual(ordered_items[1].name, "A3 Paper")

	def test_save_new_order_with_invalid_ordered_item(self):
		order = Order(product_owner_id=self.test_user, client_name="customer1", client_email="customer1@gmail.com", client_phone="08149672890", order_date="2025-07-20")
		ordered_product = OrderedProduct(name="Invalid item", quantity=4, price=30)
		order.ordered_products_objects = [ordered_product]
		self.assertEqual(order.save(), {"Invalid Item": ["'Invalid Item' doesn't exist in the Inventory."]})

		order = Order(product_owner_id=self.test_user, client_name="customer1", client_email="customer1@gmail.com", client_phone="08149672890", order_date="2025-07-20")
		ordered_product = OrderedProduct(name="Satchet Water", quantity=501, price=20)
		order.ordered_products_objects = [ordered_product]
		self.assertEqual(order.save(), {
			"Satchet Water": [
				"Not enough products in stock to satisfy order for 'Satchet Water'",
				"Price isn't the same as that of inventory item for 'Satchet Water'"
			]
		})

	def test_add_new_valid_product_to_order(self):
		order = Order(product_owner_id=self.test_user, client_name="customer3", client_email="customer3@gmail.com", client_phone="07146372890", order_date="2025-07-20")
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
		order = Order(product_owner_id=self.test_user, client_name="customer2", client_email="customer2@gmail.com", client_phone="08146272890", order_date="2025-07-20")
		ordered_product_1 = OrderedProduct(name="Satchet Water", quantity=5, price=30)
		order.ordered_products_objects = [ordered_product_1]
		order.save()
		ordered_product_2 = OrderedProduct(name="Satchet Water", order_id=order, quantity=1, price=30)
		self.assertRaises(IntegrityError, ordered_product_2.save)


class OrderedProductModelTest(TestCase):
	# data_validation, constraints, max_length e.t.c.

	@classmethod
	def setUp(cls):
		cls.test_user = CustomUser.objects.create(business_name="melon inc.", full_name="Melon Tusk", email="melontusk@gmail.com", password="12345678")
		cls.product_1 = Inventory.objects.create(owner=cls.test_user, product_name="Water Melon", price=1500, stock_level=200, date_added="2025-05-15")
		cls.product_2 = Inventory.objects.create(owner=cls.test_user, product_name="Winter Melon", price=2000, stock_level=200, date_added="2025-05-15")
		cls.product_3 = Inventory.objects.create(owner=cls.test_user, product_name="Cantaloupe", price=1000, stock_level=200, date_added="2025-05-15")

		cls.test_order = Order(product_owner_id=cls.test_user, client_name="melon-client", order_date="2025-06-15")
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
		new_order = Order(product_owner_id=self.test_user, client_name="bob", order_date="2025-07-21")
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
		actual_order = existing_ordered_item.order_id

		new_order = Order(product_owner_id=self.test_user, client_name="Ace", order_date="2025-06-20")
		new_ordered_product = OrderedProduct(name="Water Melon", quantity=2, price=1500)
		new_order.ordered_products_objects = [new_ordered_product]
		new_order.save()

		existing_ordered_item.order_id = new_order
		update_errors = existing_ordered_item.save()
		existing_ordered_item = OrderedProduct.objects.get(pk=self.item.id)
		self.assertEqual(update_errors, ["Only 'quantity' field can be updated"])
		self.assertEqual(existing_ordered_item.order_id, actual_order)

		existing_ordered_item.cummulative_price = 3
		update_errors = existing_ordered_item.save()
		existing_ordered_item = OrderedProduct.objects.get(pk=self.item.id)
		self.assertEqual(update_errors, ["Only 'quantity' field can be updated"])
		self.assertEqual(existing_ordered_item.cummulative_price, 3000)

		existing_ordered_item.name = "Cantaloupe"
		existing_ordered_item.price = 1000
		update_errors = existing_ordered_item.save()
		existing_ordered_item = OrderedProduct.objects.get(pk=self.item.id)
		self.assertEqual(update_errors, ["Only 'quantity' field can be updated"])
		self.assertEqual(existing_ordered_item.name, "Water Melon")

	def test_delete_only_ordered_item_of_order(self):
		self.assertRaises(ValueError, OrderedProduct.objects.get(pk=self.item.id).delete)

	def test_valid_ordered_item_delete(self):
		new_order = Order(product_owner_id=self.test_user, client_name="bob", order_date="2025-07-20")
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
		product = Inventory.objects.create(owner=self.test_user, product_name="Snap Melon", price=500, stock_level=100, date_added="2025-05-15")
		new_order = Order(product_owner_id=self.test_user, client_name="Marla", order_date="2025-04-20")
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
	
