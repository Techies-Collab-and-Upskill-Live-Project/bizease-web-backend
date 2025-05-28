from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class CustomUserManager(BaseUserManager):
	def model(self, *args, **kwargs):
		print("got_em")
		super().model(*args, **kwargs)

	def create_user(self, email, password, **extra_fields):
		print("broooo!")
		if not email:
			raise ValueError('Email is required')
		email = self.normalize_email(email)
		print(email, password)
		return
		user = self.model(email=email, **extra_fields)
		user.set_password(password)
		user.save()
		return user

	def create_superuser(self, email, password, **extra_fields):
		print(email)
		extra_fields.setdefault('is_staff', True)
		extra_fields.setdefault('is_superuser', True)
		extra_fields.setdefault('is_active', True)

		if extra_fields.get('is_staff') is not True:
			raise ValueError('super user must be a staff')

		if extra_fields.get('is_superuser') is not True:
			raise ValueError('super user must be a superuser obviously')

		return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
	business_name = models.CharField(max_length=200, unique=True)
	full_name = models.CharField(max_length=200)
	email = models.CharField(_('Email Address'), max_length=150, unique=True) # email and password for logging in
	business_email = models.CharField(max_length=150, unique=True, blank=True, null=True)
	CURRENCY_CHOICES = {"USD": "United States dollar", "NGN": "Nigerian naira", "GBP": "Pound sterling"}
	currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default="NGN")
	business_type = models.CharField(max_length=150, blank=True)
	password = models.CharField(max_length=50)
	COUNTRY_CHOICES = {"United States": "United States", "Nigeria": "Nigeria"}
	country = models.CharField(choices=COUNTRY_CHOICES, default="Nigeria");
	state = models.CharField(max_length=100, blank=True)
	date_joined = models.DateTimeField(_("date joined"), default=timezone.now)
	is_staff = models.BooleanField(default=False)
	is_active = models.BooleanField(default=True)

	USERNAME_FIELD = 'email'
	REQUIRED_FIELDS = []
	objects = CustomUserManager()

	# users table would need some form of low_stock_alert_threshold col if we are following design then
	# all requests should have some form of currency field then

	def __str__(self):
		return self.email