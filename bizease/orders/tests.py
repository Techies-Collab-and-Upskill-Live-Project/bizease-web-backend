from django.test import TestCase
from .models import Order, OrderedProduct
from accounts.models import CustomUser
from inventory.models import Inventory
from django.db.utils import IntegrityError

# Things to test
# Orders Model
# ordered_product_serializer
# order serializer
# Creating new order with the serializer
# Updating existing order with the Serializer
# Add new product to an Order
# Delete product from an Order
# Introduce errors on purpose to test how well the transactions work

# Delete product from an Delete product from an OrderDelete product from an OrderDelete product from an OrderDelete product from an OrderDelete product from an Order

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
		self.assertEqual(order.save(), {"Invalid item": ["'Invalid item' doesn't exist in the Inventory."]})

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


"""
class OrderedProductModelTest(TestCase):

	def test_save_new_model_instance(self):

class OrderSerializersTest(TestCase):
	@class_method
	def setUpData(cls):
		cls.test_user = CustomUser.objects.create(
			business_name="Business 2", full_name="Business Man 2", email="businessman2@email.com", password="12345678"
		)
		cls.product_1 = Inventory.objects.create(owner=cls.test_user, product_name="Bread", price=500, stock_level=50)
		cls.product_3 = Inventory.objects.create(owner=cls.test_user, product_name="Pen", price=100, stock_level=105)
		cls.product_4 = Inventory.objects.create(owner=cls.test_user, product_name="Detergent", price=800, stock_level=75)

		cls.test_order_1 = Order.objects.create(
			product_owner_id=test_user, client_name="client1", client_email="clientemail@gmail.com", client_phone="08048672894",
		)

		cls.ordered_product_1 = OrderedProduct(name="Pen", order_id=cls.test_order_1.id, quantity=40, price=100)
		cls.ordered_product_1.save(cls.test_user.id)
		cls.ordered_product_2 = OrderedProduct(name="Bread", order_id=cls.test_order_1.id, quantity=6, price=500)
		cls.ordered_product_2.save(cls.test_user.id)
		cls.ordered_product_3 = OrderedProduct(name="Detergent", order_id=cls.test_order_1.id, quantity=3, price=800)
		cls.ordered_product_3.save(cls.test_user.id)

	def test_order_serialization(self):
		expected_output = {
			"id": cls.test_order_1.id,
			"status": "Pending",
			"client_name": "client1",
			"client_email": "clientemail@gmail.com",
			"client_phone": "08048672894",
			"order_date": cls.test_order_1.order_date.isoformat().replace('+00:00', 'Z'),
			"delivery_date": None,
			"total_price": 0,
			"ordered_product": [

			]
		}
"""