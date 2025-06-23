from .models import Inventory
from rest_framework.views import APIView
from .serializers import InventoryItemSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum, F, Q
from django.db.utils import IntegrityError
import math

"""
{"product_name": "Cup", "description": "Drink Water", "price": "10000"}
"""

class InventoryStatsView(APIView):
	permission_classes = [IsAuthenticated]
	parser_classes = [JSONParser]
	
	# Inventory.objects.aggregate(total=Sum("stock_level")) # total no of individual items in inventory. Is this what was meant by total products?
	def get(self, request, **kwargs):
		data = {
			"total_stock_value": Inventory.objects.filter(owner=request.user.id).aggregate(total=Sum(F("stock_level") * F("price")))["total"],
			"low_stock_count": Inventory.objects.filter(owner=request.user.id).filter(stock_level__lte=F("low_stock_threshold")).count(),
			"total_products":  Inventory.objects.filter(owner=request.user.id).count(),
		}
		return Response({"data": data}, status=status.HTTP_200_OK)

class InventoryView(APIView):
	permission_classes = [IsAuthenticated]
	parser_classes = [JSONParser]
	page_size = 20
	curr_queryset = None

	def filter_by_query_param(self):
		# query - searches thru product_name and description (inexact) . Will serve as the search endpoint
		query_str = self.request.GET.get('query')
		if not query_str or len(self.request.GET.getlist('query')) != 1:
			return self
		self.curr_queryset = self.curr_queryset.filter(
			Q(product_name__icontains=query_str) | Q(description__icontains=query_str)
		)
		return self

	def filter_by_category_param(self):
		category = self.request.GET.get('category')
		if not category or len(self.request.GET.getlist('category')) != 1:
			return self

		self.curr_queryset = self.curr_queryset.filter(category__iexact=category)
		return self

	def order_by_query(self):
		valid_values  = ["id", "-id", "last_updated", "-last_updated", "-price", "price"]

		order_query = self.request.GET.get('order')
		if order_query not in valid_values or len(self.request.GET.getlist('order')) != 1:
			return self

		self.curr_queryset = self.curr_queryset.order_by(order_query)
		return self

	def get_page_param(self):
		page_param = self.request.GET.get('page')
		if not page_param or len(self.request.GET.getlist('page')) != 1:
			return None
		try:
			return int(page_param)
		except:
			return None

	def filter_low_Stock(self):
		if 'low_stock' not in self.request.GET:
			return self

		self.curr_queryset = self.curr_queryset.filter(stock_level__lte=F("low_stock_threshold"))
		return self

	def get(self, request, **kwargs):
		self.curr_queryset = Inventory.objects.filter(owner=request.user.id)
		self.filter_by_query_param().filter_by_category_param().filter_low_Stock().order_by_query()

		page_param = self.get_page_param()

		if page_param:
			page_count = math.ceil(len(self.curr_queryset)/self.page_size)
			if (page_count < page_param) or (page_param <= 0):
				return Response({"detail": "Page Not found", "data": None}, status=status.HTTP_404_NOT_FOUND)

			offset = (page_param-1) * self.page_size
			self.curr_queryset = self.curr_queryset[offset:offset+self.page_size]
		else:
			page_count = 1
		inventory_serializer = InventoryItemSerializer(list(self.curr_queryset), many=True)


		if page_param and (page_param+1 <= page_count):
			next_page = page_param + 1
		else:
			next_page = None

		if page_param and (page_param-1 >= 1):
			prev_page = page_param - 1
		else:
			prev_page = None

		data = {
			"page_count": page_count,
			"next_page": next_page,
			"prev_page": prev_page,
			"length": len(inventory_serializer.data),
			"products": inventory_serializer.data
		}
		return Response({"data": data}, status=status.HTTP_200_OK)

	def post(self, request, **kwargs):
		serializer = InventoryItemSerializer(data=request.data)
		if not serializer.is_valid():
			return Response({"detail": serializer.errors}, status=400)
		else:
			db_saved_item = None
			try:
				db_saved_item = serializer.save(request.user)
			except IntegrityError:
				return Response({"detail": "Multiple inventory items with the same 'product_name' are not allowed"}, status=status.HTTP_200_OK)

			return Response({"detail": "New Item added to inventory", "data": InventoryItemSerializer(db_saved_item).data}, status=status.HTTP_200_OK)

class InventoryItemView(APIView):
	permission_classes = [IsAuthenticated]
	parser_classes = [JSONParser]

	def get(self, request, item_id, **kwargs):
		try:
			item = Inventory.objects.get(pk=item_id)
		except Inventory.DoesNotExist:
			return Response({"detail": "Item not found"}, status=status.HTTP_404_NOT_FOUND)
		except Inventory.MultipleObjectsReturned: # This shouldn't be possible but it's handled anyways
			return Response({"detail": "Target happens to be multiple items"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

		inventory_item = InventoryItemSerializer(item)
		return Response(inventory_item.data, status=status.HTTP_200_OK)

	def put(self, request, item_id, **kwargs):
		try:
			item = Inventory.objects.get(pk=item_id)
		except Inventory.DoesNotExist:
			return Response({"detail": "Item not found"}, status=status.HTTP_404_NOT_FOUND)
		except Inventory.MultipleObjectsReturned: # This shouldn't be possible but it's handled anyways
			return Response({"detail": "Target happens to be multiple items"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

		productDataUpdate = InventoryItemSerializer(item, data=request.data, partial=True)
		if productDataUpdate.is_valid():
			productDataUpdate.save(request.user)
			return Response({"detail": "Product data updated successful"}, status=status.HTTP_200_OK)
		else:
			return Response(
				{"detail": productDataUpdate.errors}, 
				status=status.HTTP_400_BAD_REQUEST
			)

	def delete(self, request, item_id, **kwargs):
		try:
			item = Inventory.objects.get(pk=item_id)
		except Inventory.DoesNotExist:
			return Response({"detail": "Item not found"}, status=status.HTTP_404_NOT_FOUND)
		except Inventory.MultipleObjectsReturned: # This shouldn't be possible but it's handled anyways
			return Response({"detail": "Target happens to be multiple"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

		del_count, del_dict = item.delete()
		if (del_count > 0):
			return Response({"detail": "Inventory Item deleted successfully"}, status=status.HTTP_200_OK)
		else: # What could go wrong?
			return Response(
				{"detail": "Delete operation incomplete. Something went wrong while deleting inventory Item"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
			)