from rest_framework.parsers import JSONParser
from .models import CustomUser
from .serializers import SignUpDataSerializer, LoginDataSerializer, ProfileDataSerializer
from django.contrib.auth import authenticate # , login
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status,generics
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework.views import APIView
from django.core.mail import EmailMultiAlternatives
import os
import random
from datetime import datetime, timezone, timedelta
# from google_auth_oauthlib.flow import InstalledAppFlow


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


class EmailVerificationView(APIView):
    def post(self, request, version):
        try:
            user = CustomUser.objects.get(email=request.data.get("email"))
        except (CustomUser.DoesNotExist):
            return Response({"detail": "Invalid email"}, status=400)

        values = user.email_verification_token.split("_")
        valid_otp = values[0]
        time_created = values[1]
        otp_expired = (datetime.now(timezone.utc) - datetime.fromisoformat(time_created)) > timedelta(hours=24)

        if request.data.get("otp") == valid_otp and not otp_expired:
            user.is_active = True
            user.email_verification_token = None
            user.save()
            return Response({"detail": "User email verified."}, status=200)
        return Response({"detail": "Invalid or expired otp"}, status=400)


def send_email_verification_code(base_url, email):
    user = CustomUser.objects.filter(email=email).first()
    otp = random.randint(100000, 999999)
    if user:
        subject="Bizease Email Verification Request"
        html_content = (
            f"""<p>Here's the otp to verify your email address: <strong>{otp}</strong>. It expires in the next 24 hours.</p>
            <p>If you didn't create this account, just ignore this email.</p>"""
        )
        text_content = (
            f"Here's the otp to verify your email address: <strong>{otp}</strong>. It expires in the next 24 hours.\n"
            "If you didn't create this account, just ignore this email."
        )
        mail = EmailMultiAlternatives(subject, text_content, os.getenv("EMAIL_HOST_USER"), [email])
        mail.attach_alternative(html_content, "text/html")
        mail.send()
        user.email_verification_token = str(otp) + "_" + datetime.now(timezone.utc).isoformat()
        user.save()


class SendEmailVerification(APIView):
    def post(self, request, version):
        try:
            newUser = CustomUser.objects.get(email=request.data.get("email"))
        except CustomUser.DoesNotExist:
            pass

        else:
            if not newUser.is_active:
                send_email_verification_code(request.get_host(), newUser.email)
        
        # Always return success to prevent user enumeration
        return Response({"detail": "Email verification has been sent if the email is registered"}, status=status.HTTP_200_OK)


class SignUpView(APIView):
    parser_classes = [JSONParser]

    def post(self, request, **kwargs):
        serializer = SignUpDataSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        newUser = serializer.save()
        send_email_verification_code(request.get_host(), newUser.email)
        return Response({"detail": "User account created. Email verification has been sent"}, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    parser_classes = [JSONParser]

    def post(self, request, **kwargs):
        serializer = LoginDataSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        if not CustomUser.objects.get(email=serializer.data["email"]).is_active:
            return Response({"detail": "Unverified account! Please verify your account."}, status=status.HTTP_401_UNAUTHORIZED)

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
	
class PasswordResetRequestView(APIView):
    def post(self, request, **kwargs):
        email = request.data.get("email")
        user = CustomUser.objects.filter(email=email).first()
        otp = random.randint(100000, 999999)
        if user and user.is_active:
            subject="Password Reset Request"
            html_content = (
                f"""<p>Here's the otp to reset your password: <strong>{otp}</strong>. It expires in the next 1 hour.</p>
                <p>If you didn't request for a password reset, please ignore this email</p>"""
            )
            text_content = (
                f"Here's the otp to reset your password: {otp}. It expires in the next 1 hour.\n"
                "If you didn't request for a password reset, please ignore this email"
            )
            mail = EmailMultiAlternatives(subject, text_content, os.getenv("EMAIL_HOST_USER"), [email])
            mail.attach_alternative(html_content, "text/html")
            mail.send()
            user.passwd_reset_otp_with_time_created = str(otp) + "_" + datetime.now(timezone.utc).isoformat()
            user.save()

        # Always return success to prevent user enumeration
        return Response({"detail": "If the email is valid, a password reset otp has been sent."}, status=200)

class PasswordResetConfirmView(APIView):
    def post(self, request, **kwargs):
        try:
            user = CustomUser.objects.get(email=request.data.get("email"))
        except (CustomUser.DoesNotExist):
            return Response({"detail": "Invalid email"}, status=400)

        values = user.passwd_reset_otp_with_time_created.split("_")
        valid_otp = values[0]
        time_created = values[1]
        otp_expired = (datetime.now(timezone.utc) - datetime.fromisoformat(time_created)) > timedelta(hours=1)

        if request.data.get("otp") == valid_otp and not otp_expired:
            new_password = request.data.get("password")
            user.set_password(new_password)
            user.passwd_reset_otp_with_time_created = None
            user.save()
            return Response({"detail": "Password has been reset."}, status=200)
        return Response({"detail": "Invalid or expired otp"}, status=400)


class GoogleAuthView(APIView):
    def post(self, request, **kwargs):
        email=request.data.get("email")
        name=request.data.get("name")

        if not email or not name:
            return Response({"detail": "Invalid email or name field"}, status=400)

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            user = CustomUser(
                full_name=name,
                business_name=f"{name}'s Biz",
                business_type="Sole proprietorship",  # default
                currency="NGN",
                country="Nigeria",
                state=""
            )
            user.set_password(''.join(random.choices(string.ascii_uppercase + string.digits, k=10)))
            user.save()

        tokens = get_tokens_for_user(user)
        return Response({
            "detail": "Login successful",
            "data": tokens
        }, status=200)