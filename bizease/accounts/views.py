from rest_framework.parsers import JSONParser
from .models import CustomUser
from .serializers import SignUpDataSerializer, LoginDataSerializer, ProfileDataSerializer
from django.contrib.auth import authenticate # , login
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status,generics
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.urls import reverse
from rest_framework.views import APIView
from rest_framework.response import Response
from allauth.socialaccount.models import SocialAccount

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

"""
{"business_name ": "", "full_name": "", "email": "", "business_email": "", "currency": "", 
"business_type": "", "password": "", "country": "", "state": "", "low_stock_threshold": 0}

https://adedamola.pythonanywhere.com/
"""

class SignUpView(APIView):
	parser_classes = [JSONParser]

	def post(self, request, **kwargs):
		serializer = SignUpDataSerializer(data=request.data)
		if not serializer.is_valid():
			return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
		else:
			newUser = serializer.save()
		tokens = get_tokens_for_user(newUser)
		return Response({"detail": "User Created successfully", "data": tokens}, status=status.HTTP_201_CREATED)


class LoginView(APIView):
	parser_classes = [JSONParser]

	def post(self, request, **kwargs):
		serializer = LoginDataSerializer(data=request.data)

		if not serializer.is_valid():
			return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

		user = authenticate(request, username=serializer.data["email"], password=serializer.data["password"])
		if not user:
			return Response({"detail": "Invalid credentials!"}, status=status.HTTP_401_UNAUTHORIZED)

		tokens = get_tokens_for_user(user)
		return Response({"detail": "Login successful", "data": tokens}, status=status.HTTP_200_OK)


class ProfileView(APIView):
	permission_classes = [IsAuthenticated]
	parser_classes = [JSONParser]

	def get(self, request, **kwargs):
		userProfileDict = ProfileDataSerializer(request.user).data
		return Response({"data": userProfileDict}, status=status.HTTP_200_OK)

	def put(self, request, **kwargs):
		dataUpdate = ProfileDataSerializer(request.user, data=request.data, partial=True)
		if dataUpdate.is_valid():
			if dataUpdate.validated_data.get("field_errors"):
				return Response({"detail": dataUpdate.validated_data["field_errors"]}, status=status.HTTP_200_OK)
			result = dataUpdate.save()
			return Response({"detail": "User data updated successfully"}, status=status.HTTP_200_OK)
		else:
			return Response({"detail": dataUpdate.errors}, status=status.HTTP_400_BAD_REQUEST)

	def delete(self, request, **kwargs):
		del_count, del_dict = request.user.delete()
		if (del_count > 0):
			return Response({"detail": "User data deleted successfully"}, status=status.HTTP_200_OK)
		else: # What could go wrong?
			return Response(
				{"detail": "Delete operation incomplete. Something went wrong while deleting user data"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
			)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def delete(self, request, **kwargs):
        token_str = request.headers.get("x-session-refresh-token")

        if not token_str:
            return Response(
                {"detail": "'x-session-refresh-token' http header with a valid refresh token value must be present"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token_to_blacklist = RefreshToken(token_str)
            token_to_blacklist.blacklist()
        except TokenError as err:
            return Response(
                {"detail": "Invalid refresh token value"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except:
            return Response({"detail": "Something went wrong! Please try again"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"detail": "User logged out"}, status=status.HTTP_200_OK)
	
import os
class PasswordResetRequestView(APIView):
    def post(self, request):
        email = request.data.get("email")
        user = CustomUser.objects.filter(email=email).first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_link = f"{request.get_host()}/auth/password-reset-confirm/{uid}/{token}/"
            send_mail(
                subject="Password Reset Request",
                message=f"Click the link to reset your password: {reset_link}",
                from_email=os.getenv("EMAIL_HOST_USER"),
                recipient_list=[email],
            )
        # Always return success to prevent user enumeration
        return Response({"detail": "If the email is valid, a reset link has been sent."}, status=200)

class PasswordResetConfirmView(APIView):
    def post(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = CustomUser.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            return Response({"detail": "Invalid link"}, status=400)

        if default_token_generator.check_token(user, token):
            new_password = request.data.get("password")
            user.set_password(new_password)
            user.save()
            return Response({"detail": "Password has been reset."}, status=200)
        return Response({"detail": "Invalid or expired token"}, status=400)
	
import requests
GOOGLE_TOKEN_INFO_URL = "https://oauth2.googleapis.com/tokeninfo"


class GoogleAuthView(APIView):
    def post(self, request):
        id_token = request.data.get("id_token")
        if not id_token:
            return Response({"detail": "ID token is required"}, status=400)

        # Verify token with Google
        response = requests.get(GOOGLE_TOKEN_INFO_URL, params={'id_token': id_token})
        if response.status_code != 200:
            return Response({"detail": "Invalid Google token"}, status=400)

        user_info = response.json()
        email = user_info.get("email")
        full_name = user_info.get("name")

        if not email:
            return Response({"detail": "Google token did not return email"}, status=400)

        # Check if user exists
        user, created = CustomUser.objects.get_or_create(
            email=email,
            defaults={
                "full_name": full_name,
                "business_name": f"{full_name}'s Biz",
                "business_type": "Sole proprietorship",  # default
                "currency": "NGN",
                "country": "Nigeria",
                "state": "",
                "password": CustomUser.objects.make_random_password(),
            }
        )

        tokens = get_tokens_for_user(user)
        return Response({
            "detail": "Login successful",
            "data": tokens
        }, status=200)