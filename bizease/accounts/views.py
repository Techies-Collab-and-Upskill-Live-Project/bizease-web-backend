from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser
from .models import CustomUser
from .serializers import UserDataSerializer, LoginDataSerializer
from django.contrib.auth import authenticate # , login

"""
The server must generate an Allow header in a 405 response with a list of methods that the target resource currently supports.
"""

"""
{"business_name ": "", "full_name": "", "email": "", "business_email": "", "currency": "", 
"business_type": "", "password": "", "country": "", "state": "", "low_stock_threshold": 0}
"""

@csrf_exempt
def signup(request):
	if request.method != 'POST':
		return JsonResponse({"errorMSg": "Only POST request is supported"}, status=405)

	data = JSONParser().parse(request) # transforms the request's json payload into a python dict
	serializer = UserDataSerializer(data=data) # serializes 'data' for further processing
	if not serializer.is_valid():
		return JsonResponse({"errors": serializer.errors}, status=400)
	else:
		serializer.save()
		return JsonResponse({"msg": "User Created successfully"}, status=200)


@csrf_exempt
def login(request):
	if request.method != 'POST':
		return JsonResponse({"errorMSg": "Only POST request is supported"}, status=405)

	data = JSONParser().parse(request) # transforms the request's json payload into a python dict
	serializer = LoginDataSerializer(data=data) # serializes 'data' for further processing
	serializer.is_valid()
	if (serializer.errors):
		return JsonResponse({"errors": serializer.errors}, status=400)

	User = authenticate(request, username=serializer.data["email"], password=serializer.data["password"])
	if not User:
		return JsonResponse({"msg": "Not recognized. pls sign up"}, status=401)

	# todo: set up user session using jwt
	return JsonResponse({"msg": "my bro"}, status=200)