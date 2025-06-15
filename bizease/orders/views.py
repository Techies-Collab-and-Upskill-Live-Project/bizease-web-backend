from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from .serializers import OrderSerializer
from rest_framework.response import Response
from .models import Order
from rest_framework import status
from django.db.models import Sum, F
import math


class OrderStatsView(APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request, **kwargs):
		data = {
			"total_orders": Order.objects.filter(product_owner_id=request.user.id).count(),
			"total_revenue": Order.objects.filter(product_owner_id=request.user.id).aggregate(Sum("total_price"))['total_price__sum'],
			"pending_orders": Order.objects.filter(product_owner_id=request.user.id).filter(status="Pending").count()
		}
		return Response({"data": data}, status=status.HTTP_200_OK)

class OrdersView(APIView):
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

	# todo:
	# add the following get params
	# query - Orderedproduct_name, client_name (inexact) . Will serve as the search endpoint
	# status
	# order - id, order_date, total_price
	def get(self, request, **kwargs):
		page_param = self.get_page_param(request.GET)

		if not page_param:
			page_count = 1
			serializer = OrderSerializer(
				list(Order.objects.filter(product_owner_id=request.user.id).order_by("id")), 
				many=True
			)
		else:
			items_count = Order.objects.count() # total number of distinct Order
			page_count = math.ceil(items_count/self.page_size)
			if page_count < page_param:
				return Response({"detail": "Page Not found", data: None}, status=status.HTTP_404_NOT_FOUND)

			offset = (page_param-1) * self.page_size
			serializer = OrderSerializer(
				list(Order.objects.filter(product_owner_id=request.user.id).order_by("id")[offset:offset+self.page_size]),
				many=True
			)
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
			"length": len(serializer.data),
			"orders": serializer.data
		}
		# Tell frontend that id is order_id and they should reformat it to look fancy or whatever
		return Response({"data": data}, status=status.HTTP_200_OK)

	def post(self, request, **kwargs):
		order_serializer = OrderSerializer(data=request.data)
		if order_serializer.is_valid():
			response = order_serializer.save(request.user)
			return Response({"detail": response["detail"]}, status=response["status"])
		else:
			return Response({"detail": order_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class SingleOrderView(APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request, item_id, **kwargs):
		try:
			item = Order.objects.get(pk=item_id)
		except Order.DoesNotExist:
			return Response({"detail": "Item not found"}, status=status.HTTP_404_NOT_FOUND)
		except Order.MultipleObjectsReturned: # This shouldn't be possible but it's handled anyways
			return Response({"detail": "Target happens to be multiple items"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
		return Response({"data": OrderSerializer(item).data}, status=status.HTTP_200_OK)

	def put(self, request, item_id, **kwargs):
		try:
			order_to_edit = Order.objects.get(pk=item_id)
		except Order.DoesNotExist:
			return Response({"detail": "Item not found"}, status=status.HTTP_404_NOT_FOUND)
		except Order.MultipleObjectsReturned: # This shouldn't be possible but it's handled anyways
			return Response({"detail": "Target happens to be multiple items"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
		order_edits = OrderSerializer(order_to_edit, data=request.data, partial=True)

		if order_edits.is_valid():
			response = order_edits.save(request.user)
			return Response({"detail": response["detail"]}, status=response["status"])
		else:
			return Response({"detail": order_edits.errors}, status=status.HTTP_400_BAD_REQUEST)

	def delete(self, request, item_id, **kwargs):
		try:
			item = Order.objects.get(pk=item_id)
		except Order.DoesNotExist:
			return Response({"detail": "Item not found"}, status=status.HTTP_404_NOT_FOUND)
		except Order.MultipleObjectsReturned: # This shouldn't be possible but it's handled anyways
			return Response({"detail": "Target happens to be multiple items"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

		# prevent the deletion of delivered orders
		del_count, del_dict = item.delete()
		if (del_count > 0):
			return Response({"detail": "Order deleted successfully"}, status=status.HTTP_200_OK)
		else: # What could go wrong?
			return Response(
				{"detail": "Delete operation incomplete. Something went wrong while deleting inventory Item"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
			)
