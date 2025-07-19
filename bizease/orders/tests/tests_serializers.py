from django.test import TestCase
from orders.models import Order, OrderedProduct
from orders.serializers import OrderedProductSerializer, OrderSerializer
from accounts.models import CustomUser
from inventory.models import Inventory


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
		# actually been saved to the db. Making sure they are not just attributes on this instance
		updated_order = Order.objects.get(pk=updated_order.id)

		self.assertEqual(updated_order.client_name, "client_1")
		self.assertEqual(updated_order.client_email, "client_1@gmail.com")
		self.assertEqual(updated_order.client_phone, "07048673894")
		self.assertEqual(updated_order.status, "Delivered")
		self.assertEqual(updated_order.total_price, 9400)
		self.assertRegex(updated_order.order_date.isoformat().replace('+00:00', 'Z'), r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{6}Z$')
		self.assertRegex(updated_order.delivery_date.isoformat().replace('+00:00', 'Z'), r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{6}Z$')
		self.assertEqual(updated_order.ordered_products.count(), 3)

