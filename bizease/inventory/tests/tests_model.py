from django.test import TransactionTestCase
from inventory.models import Inventory
from accounts.models import CustomUser
from django.db.utils import IntegrityError

class InventorModelTest(TransactionTestCase):
	def test_user_product_name_combo_uniqueness(self):
		test_user = CustomUser.objects.create(
			business_name="Test inc.", full_name="test user", email="testuser@gmail.com", business_email="inventorytestuser@testbiz.com",
			currency="NGN", business_phone="08134568765", business_type="Limited liability company (LLC)", password="12345678", is_active=True
		)
		product_1 = Inventory(owner=test_user, product_name="Alarm clock", stock_level=50, price=7000)
		product_1.save()
		product_2 = Inventory(owner=test_user, product_name="Alarm clock", stock_level=30, price=30000)
		self.assertRaises(IntegrityError, product_2.save)

	def test_product_price_gt_zero_constraint(self):
		test_user = CustomUser.objects.create(
			business_name="business 1", full_name="user 1", email="user1@gmail.com", 
			business_email="user1@testmail.com", password="12345678", is_active=True
		)
		product_1 = Inventory(owner=test_user, product_name="product 1", stock_level=50, price=0)
		self.assertRaises(IntegrityError, product_1.save)
		product_2 = Inventory(owner=test_user, product_name="product 2", stock_level=30, price=-500)
		self.assertRaises(IntegrityError, product_2.save)

	def test_str_representation(self):
		new_user = CustomUser.objects.create(
			business_name="business 1", full_name="user 1", email="user1@gmail.com", 
			business_email="user1@testmail.com", password="12345678", is_active=True
		)
		product_1 = Inventory(owner=new_user, product_name="product 2", stock_level=30, price=1500)
		product_1.save()
		self.assertEqual(str(product_1), "product 2 - 1500")

		