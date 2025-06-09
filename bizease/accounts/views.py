from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser
from .models import CustomUser
from .serializers import SignUpDataSerializer, LoginDataSerializer, ProfileDataSerializer
from django.contrib.auth import authenticate # , login
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

"""
{"business_name ": "", "full_name": "", "email": "", "business_email": "", "currency": "", 
"business_type": "", "password": "", "country": "", "state": "", "low_stock_threshold": 0}
"""

class SignUpView(APIView):
	def post(self, request, **kwargs):
		serializer = SignUpDataSerializer(data=request.data)
		if not serializer.is_valid():
			return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
		else:
			newUser = serializer.save()
		# todo: log the user in too?
		tokens = get_tokens_for_user(newUser)
		return Response({"msg": "User Created successfully", "auth_tokens": tokens}, status=status.HTTP_200_OK)


class LoginView(APIView):
	def post(self, request, **kwargs):
		serializer = LoginDataSerializer(data=request.data)

		if not serializer.is_valid():
			return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

		user = authenticate(request, username=serializer.data["email"], password=serializer.data["password"])
		if not user:
			return Response({"msg": "Invalid credentials!"}, status=status.HTTP_401_UNAUTHORIZED)

		tokens = get_tokens_for_user(user)
		return Response({"msg": "Login successful", "auth_tokens": tokens}, status=status.HTTP_200_OK)


class ProfileView(APIView):
	def get(self, request, **kwargs):
		if (request.user.is_authenticated):
			userProfileDict = ProfileDataSerializer(request.user).data
			return Response({"data": userProfileDict}, status=status.HTTP_200_OK)
		return Response({"msg": "Unauthenticated Request. Please Login!"}, status=status.HTTP_401_UNAUTHORIZED)

	def put(self, request, **kwargs):
		if (request.user.is_authenticated):
			dataUpdate = ProfileDataSerializer(request.user, data=request.data, partial=True)
			if dataUpdate.is_valid():
				dataUpdate.save()
				return Response({"msg": "User data updated successful"}, status=status.HTTP_200_OK)
			else:
				return Response(
					{"msg": "One or more Invalid fields are present", "errors": dataUpdate.errors}, 
					status=status.HTTP_400_BAD_REQUEST
				)
		return Response({"msg": "Unauthenticated Request. Please Login!"}, status=status.HTTP_401_UNAUTHORIZED)

	def delete(self, request, **kwargs):
		if (request.user.is_authenticated):
			del_count, del_dict = request.user.delete()
			if (del_count > 0):
				return Response({"msg": "User data deleted successfully"}, status=status.HTTP_200_OK)
			else: # What could go wrong?
				return Response(
					{"msg": "Delete operation incomplete. Something went wrong while deleting user data"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
				)
		return Response({"msg": "Unauthenticated Request. Please Login!"}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
	def delete(self, request, **kwargs):
		if (request.user.is_authenticated):
			# remove the token
			return Response({"msg": "User logged out"}, status=status.HTTP_200_OK)
		return Response({"msg": "Unauthenticated Request. Please Login!"}, status=status.HTTP_401_UNAUTHORIZED)
