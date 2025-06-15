from .models import Inventory
from rest_framework.views import APIView
from .serializers import InventoryItemSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum, F
import math


class InventoryView(APIView):
	permission_classes = [IsAuthenticated]
	page_size = 20

	def get_page_param(self, get_obj):
		page_param = get_obj.get('page')
		if not page_param or len(get_obj.getlist('page')) != 1:
			return None

		try:
			page_param = int(page_param)
		except:
			return None

		if page_param <= 0:
			return None
		return page_param
	
	# todo: add order_query, filter(by category, status, stock_level), search e.t.c.
	def get(self, request, **kwargs):
		page_param = self.get_page_param(request.GET)
		items_count = Inventory.objects.count() # total number of distinct products in inventory

		if not page_param:
			page_count = 1
			inventory_serializer = InventoryItemSerializer(
				list(Inventory.objects.filter(owner=request.user.id).order_by("id")), 
				many=True
			)
		else:
			page_count = math.ceil(items_count/self.page_size)
			if page_count < page_param:
				return Response({"detail": "Page Not found", "data": None}, status=status.HTTP_404_NOT_FOUND)

			offset = (page_param-1) * self.page_size
			inventory_serializer = InventoryItemSerializer(
				list(Inventory.objects.filter(owner=request.user.id).order_by("id")[offset:offset+self.page_size]),
				many=True
			)

		# Inventory.objects.aggregate(total=Sum("stock_level")) # total no of individual items in inventory. Is this what was meant by total products?
		total_stock_value = Inventory.objects.aggregate(total=Sum(F("stock_level") * F("price")))
		low_stock_count = Inventory.objects.filter(stock_level__lte=F("low_stock_threshold")).count()

		if page_param and (page_param+1 <= page_count):
			next_page = page_param + 1
		else:
			next_page = None

		if page_param and (page_param-1 >= 1):
			prev_page = page_param - 1
		else:
			prev_page = None

		data = {
			"stats": {
				"total_stock_value": total_stock_value,
				"low_stock_count": low_stock_count,
				"total_products": items_count,
			},
			
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
			item = Inventory(owner=request.user, **serializer.data)
			item.save()
		return Response({"detail": "New Item added to inventory", "data": InventoryItemSerializer(item).data}, status=status.HTTP_200_OK)

class InventoryItemView(APIView):
	permission_classes = [IsAuthenticated]

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
			productDataUpdate.save()
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