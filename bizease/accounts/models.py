from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class CustomUserManager(BaseUserManager):
	def create_user(self, email, password=None, **extra_fields):
		if not email:
			raise ValueError('Email is required')
		email = self.normalize_email(email)
		user = self.model(email=email, **extra_fields)
		user.set_password(password)
		user.save()
		return user

	def create_superuser(self, email, password=None, **extra_fields):
		extra_fields.setdefault('is_staff', True)
		extra_fields.setdefault('is_superuser', True)
		extra_fields.setdefault('is_active', True)

		if extra_fields.get('is_staff') is not True:
			raise ValueError('super user must be a staff')

		if extra_fields.get('is_superuser') is not True:
			raise ValueError('super user must be a superuser obviously')

		return self.create_user(email, password, **extra_fields)


BUSINESS_CHOICES = [
	("Sole proprietorship","Sole proprietorship"),
	("General partnership","General partnership"),
	("Limited partnership","Limited partnership"),
	("Limited liability partnership (LLP)","Limited liability partnership (LLP)"),
	("C corporation","C corporation"),
	("S corporation","S corporation"),
	("Benefit corporation","Benefit corporation"),
	("Limited liability company (LLC)","Limited liability company (LLC)"),
	("Nonprofit","Nonprofit"),
	("Joint venture","Joint venture")
]

class CustomUser(AbstractBaseUser, PermissionsMixin):
	business_name = models.CharField(max_length=200, unique=True)
	full_name = models.CharField(max_length=200)
	email = models.CharField(_('Email Address'), max_length=150, unique=True) # email and password for logging in
	business_email = models.CharField(max_length=150, unique=True, null=True)
	phone = models.CharField(max_length=24, blank=True)
	business_phone = models.CharField(max_length=24, blank=True)
	business_address = models.CharField(max_length=150, blank=True)
	CURRENCY_CHOICES = {"USD": "United States dollar", "NGN": "Nigerian naira", "GBP": "Pound sterling"}
	currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default="NGN")
	business_type = models.CharField(max_length=150, blank=True, choices=BUSINESS_CHOICES)
	password = models.CharField(max_length=128)
	COUNTRY_CHOICES = {"United States": "United States", "Nigeria": "Nigeria"}
	country = models.CharField(choices=COUNTRY_CHOICES, default="Nigeria");
	state = models.CharField(max_length=100, blank=True)
	rcv_mail_for_new_orders = models.BooleanField(default=True)
	rcv_mail_for_low_stocks = models.BooleanField(default=True)
	rcv_mail_notification = models.BooleanField(default=True)
	rcv_msg_notification = models.BooleanField(default=True)
	default_order_status = models.CharField(choices=[("Pending","Pending"),("Delivered","Delivered")], default="Pending")
	language = models.CharField(max_length=50, default="English")
	low_stock_threshold = models.IntegerField(default=5)
	date_joined = models.DateTimeField(_("date joined"), default=timezone.now)
	is_staff = models.BooleanField(default=False)
	is_active = models.BooleanField(default=False)
	email_verification_token = models.CharField(max_length=64, null=True)
	passwd_reset_otp_with_time_created = models.CharField(max_length=64, null=True)

	USERNAME_FIELD = 'email'
	REQUIRED_FIELDS = []
	objects = CustomUserManager()

	class Meta:
		constraints = [models.CheckConstraint(condition=models.Q(low_stock_threshold__gte=0), name="low_stock_threshold_gte_0")]

	# all requests should have some form of currency field then

	def __str__(self):
		return self.email