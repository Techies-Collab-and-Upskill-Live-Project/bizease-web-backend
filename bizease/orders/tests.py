from django.test import TestCase
from .models import Order, OrderedProduct
from .serializers import OrderedProductSerializer, OrderSerializer
from accounts.models import CustomUser
from inventory.models import Inventory
from django.db.utils import IntegrityError


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
		# test that nothing is actually saved to the db if any error occurs or something

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


# Things to test
# Orders Model
# ordered_product_serializer
# order serializer
# Creating new order with the serializer
# Updating existing order with the Serializer
# Add new product to an Order
# Delete product from an Order
# Introduce errors on purpose to test how well the transactions work
# Is there no need for a tearDown method

# class OrderedProductModelTest(TestCase):

# 	def test_save_new_model_instance(self):

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