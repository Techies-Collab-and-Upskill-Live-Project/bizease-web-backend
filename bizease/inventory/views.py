from .models import Inventory
from rest_framework.views import APIView
from .serializers import InventoryItemSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import math

class InventoryView(APIView):
	permission_classes = [IsAuthenticated]
	page_size = 1

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
	
	# todo: add order_query
	def get(self, request, **kwargs):
		"page_count, next_page, prev_page"
		page_param = self.get_page_param(request.GET)
		items_count = Inventory.objects.count()

		if not page_param:
			inventory_serializer = InventoryItemSerializer(
				list(Inventory.objects.filter(owner=request.user.id).order_by("id")), 
				many=True
			)
		else:
			if math.ceil(items_count/self.page_size) < page_param:
				return Response({"detail": "Page Not found"}, status=status.HTTP_404_NOT_FOUND)

			offset = (page_param-1) * self.page_size
			inventory_serializer = InventoryItemSerializer(
				list(Inventory.objects.filter(owner=request.user.id).order_by("id")[offset:offset+self.page_size])
				many=True
			)
		return Response(inventory_serializer.data, status=status.HTTP_200_OK)

	def post(self, request, **kwargs):
		serializer = InventoryItemSerializer(data=request.data)
		if not serializer.is_valid():
			return Response({"errors": serializer.errors}, status=400)
		else:
			item = Inventory(owner=request.user, **serializer.data)
			item.save()
		return Response({"msg": "New Item added to inventory", "data": InventoryItemSerializer(item).data}, status=status.HTTP_200_OK)

class InventoryItemView(APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request, item_id, **kwargs):
		try:
			item = Inventory.objects.get(pk=item_id)
		except Inventory.DoesNotExist:
			return Response({"msg": "Item not found"}, status=status.HTTP_404_NOT_FOUND)
		except Inventory.MultipleObjectsReturned: # This shouldn't be possible but it's handled anyways
			return Response({"msg": "Target happens to be multiple items"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

		inventory_item = InventoryItemSerializer(item)
		return Response(inventory_item.data, status=status.HTTP_200_OK)

	def put(self, request, item_id, **kwargs):
		try:
			item = Inventory.objects.get(pk=item_id)
		except Inventory.DoesNotExist:
			return Response({"msg": "Item not found"}, status=status.HTTP_404_NOT_FOUND)
		except Inventory.MultipleObjectsReturned: # This shouldn't be possible but it's handled anyways
			return Response({"msg": "Target happens to be multiple items"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

		productDataUpdate = InventoryItemSerializer(item, data=request.data, partial=True)
		if productDataUpdate.is_valid():
			productDataUpdate.save()
			return Response({"msg": "Product data updated successful"}, status=status.HTTP_200_OK)
		else:
			return Response(
				{"msg": "One or more Invalid fields are present", "errors": productDataUpdate.errors}, 
				status=status.HTTP_400_BAD_REQUEST
			)

	def delete(self, request, item_id, **kwargs):
		try:
			item = Inventory.objects.get(pk=item_id)
		except Inventory.DoesNotExist:
			return Response({"msg": "Item not found"}, status=status.HTTP_404_NOT_FOUND)
		except Inventory.MultipleObjectsReturned: # This shouldn't be possible but it's handled anyways
			return Response({"msg": "Target happens to be multiple"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

		del_count, del_dict = item.delete()
		if (del_count > 0):
			return Response({"msg": "Inventory Item deleted successfully"}, status=status.HTTP_200_OK)
		else: # What could go wrong?
			return Response(
				{"msg": "Delete operation incomplete. Something went wrong while deleting inventory Item"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
			)