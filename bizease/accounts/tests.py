from django.test import Client
from .models import CustomUser
from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from .views import get_tokens_for_user
from .serializers import ProfileDataSerializer
from rest_framework_simplejwt.tokens import RefreshToken

class AccountsViewsTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.test_user = CustomUser(
            business_name="Test-Biz", full_name="Test User", email="testuser@testmail.com", 
            business_email="test@bizmail.com", currency="NGN", business_phone="07012356790", business_type="Nonprofit",
            state="small-naija", language="Yoruba", is_active=True
        )
        cls.test_user.set_password("GoodPassword123")
        cls.test_user.save()

        cls.unverified_user = CustomUser(business_name="Fraud Inc.", full_name="Paul Fred", email="pf419@testmail.com")
        cls.unverified_user.set_password("paul_fred")
        cls.unverified_user.save()

        cls.last_user = CustomUser(
            business_name="Clock work", full_name="clock work joe", email="joe@testmail.com", 
            business_email="main@clockwork.com", is_active=True
        )
        cls.last_user.set_password("12345678")
        cls.last_user.save()

        cls.refresh_obj = RefreshToken.for_user(cls.test_user)
        cls.access_token = str(cls.refresh_obj.access_token)

    def test_signup_view_with_valid_data(self):
        """ Ensure we can create a new User """
        url = reverse('signup', args=["v1"])
        data = {
            "business_name": "New business", "full_name": "New User", 
            "email": "newuser@testmail.com", "currency": "NGN", 
            "business_type": "Nonprofit", "password": "neworek", 
            "country": "Nigeria", "state": "Lagos"
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CustomUser.objects.count(), 4)
        new_user = CustomUser.objects.get(email="newuser@testmail.com")
        self.assertEqual(new_user.full_name, 'New User')
        self.assertNotEqual(new_user.password, 'neworek')
        self.assertEqual(response.data["detail"], "User account created. Email verification has been sent")

    def test_signup_with_existing_email(self):
        url = reverse('signup', args=["v1"])
        data = {
            "business_name": "New business", "full_name": "New User", 
            "email": "testuser@testmail.com", "currency": "NGN", 
            "business_type": "Nonprofit", "password": "neworek", 
            "country": "Nigeria", "state": "Lagos"
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.data,  {"detail": {"email": ["custom user with this Email Address already exists."]}})

    def test_signup_view_with_invalid_data(self):
        url = reverse('signup', args=["v1"])
        data = {
            "full_name": "", 
            "email": "user2@testmail.com", 
            "currency": "yyy", 
            "country": "Paradis", 
            "state": "Lagos"
        }

        response = self.client.post(url, data, format='json')
        errored_fields = response.data["detail"].keys()
        self.assertIn("business_name", errored_fields) # 'business_name' is a required field
        self.assertIn("country", errored_fields) # 'Paradis' is not a valid choice.
        self.assertIn("full_name", errored_fields) # Can't have empty values
        self.assertIn("currency", errored_fields) # 'yyy' is not a valid choice


    def test_login_view_with_valid_credentials(self):
        url = reverse('login', args=["v1"])
        data = {
            "email": "testuser@testmail.com",
            "password": "GoodPassword123"
        }

        response = self.client.post(url, data, format='json')
        # print(self.test_user.email, response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # checks if response contains access and refresh tokens
        self.assertIn("access", response.data["data"].keys())
        self.assertIn("refresh", response.data["data"].keys())

    def test_login_view_with_invalid_credentials(self):
        url = reverse('login', args=["v1"])
        data = {
            "email": "testuser@testmail.com",
            "password": "BadPassword123"
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["detail"], "Invalid credentials!")
        self.assertEqual(response.data.get("data"), None)

    def test_login_view_with_unverified_user_valid_credentials(self):
        url = reverse('login', args=["v1"])
        data = {
            "email": "pf419@testmail.com",
            "password": "paul_fred"
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["detail"], "Unverified account! Please verify your account.")
        self.assertEqual(response.data.get("data"), None)

    def test_user_profile_request(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)

        response = self.client.get(reverse("user-account-details", args=["v1"]), format='json')
        expected_data = ProfileDataSerializer(self.test_user).data
        self.assertEqual(response.data["data"], expected_data)
        expected_data_keys = expected_data.keys()
        self.assertNotIn("date_joined", expected_data_keys)
        self.assertNotIn("is_staff", expected_data_keys)
        self.assertNotIn("is_active", expected_data_keys)
        self.assertNotIn("email_verification_token", expected_data_keys)
        self.assertNotIn("passwd_reset_otp_with_time_created", expected_data_keys)

    def test_user_profile_update_request(self):
        access_token = get_tokens_for_user(self.test_user)["access"]
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)

        response = self.client.put(reverse( "user-account-details", args=["v1"]), {"full_name": "Updated Name"}, format='json')
        self.assertEqual(response.data["detail"], "User data updated successfully")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.test_user = CustomUser.objects.get(pk=self.test_user.id)
        self.assertEqual("Updated Name", self.test_user.full_name)

    def test_user_profile_delete_request(self):
        tokens = get_tokens_for_user(self.last_user)
        access_token = tokens["access"]
        refresh_token = tokens["refresh"]
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + access_token)

        response = self.client.delete(reverse("user-account-details", args=["v1"]), format='json', headers={"x-session-refresh-token": refresh_token})
        self.assertEqual(response.data["detail"], "User data deleted successfully")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertRaises(CustomUser.DoesNotExist, CustomUser.objects.get, pk=self.last_user.id)

        
