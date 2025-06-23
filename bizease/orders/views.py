from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView
from .serializers import OrderSerializer
from rest_framework.response import Response
from .models import Order
from rest_framework import status
from django.db.models import Sum, F, Q
import math


class OrderStatsView(APIView):
	permission_classes = [IsAuthenticated]
	parser_classes = [JSONParser]

	def get(self, request, **kwargs):
		data = {
			"total_orders": Order.objects.filter(product_owner_id=request.user.id).count(),
			"total_revenue": Order.objects.filter(product_owner_id=request.user.id).aggregate(Sum("total_price"))['total_price__sum'],
			"pending_orders": Order.objects.filter(product_owner_id=request.user.id).filter(status="Pending").count()
		}
		return Response({"data": data}, status=status.HTTP_200_OK)

class OrdersView(APIView):
	parser_classes = [JSONParser]
	permission_classes = [IsAuthenticated]
	page_size = 20
	curr_queryset = None

	def order_data(self):
		valid_values  = ["id", "-id", "order_date", "-order_date", "-total_price", "total_price"]

		order_query = self.request.GET.get('order')
		if order_query not in valid_values or len(self.request.GET.getlist('order')) != 1:
			return self

		self.curr_queryset = self.curr_queryset.order_by(order_query)
		return self

	def filter_data_by_query(self):
		query_str = self.request.GET.get('query')
		if not query_str or len(self.request.GET.getlist('query')) != 1:
			return self
		self.curr_queryset = self.curr_queryset.filter(
			Q(ordered_products__name__icontains=query_str) | Q(client_name__icontains=query_str)
		)
		return self

	def filter_data_by_status(self):
		valid_values  = ["Pending", "Delivered"]

		status = self.request.GET.get('status')
		if status:
			status = status.title()

		if status not in valid_values or len(self.request.GET.getlist('status')) != 1:
			return self

		self.curr_queryset = self.curr_queryset.filter(status=status)
		return self

	def get_page_param(self):
		page_param = self.request.GET.get('page')
		if not page_param or len(self.request.GET.getlist('page')) != 1:
			return None
		try:
			return int(page_param)
		except:
			return None

	def get(self, request, **kwargs):
		self.curr_queryset = Order.objects.filter(product_owner_id=request.user.id)
		self.filter_data_by_query().filter_data_by_status().order_data()

		page_param = self.get_page_param()

		if page_param:
			page_count = math.ceil(len(self.curr_queryset)/self.page_size)
			if (page_count < page_param) or (page_param <= 0):
				return Response({"detail": "Page Not found", data: None}, status=status.HTTP_404_NOT_FOUND)

			offset = (page_param-1) * self.page_size
			self.curr_queryset = self.curr_queryset[offset:offset+self.page_size]
		else:
			page_count = 1

		serializer = OrderSerializer(list(self.curr_queryset), many=True)
		
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
	parser_classes = [JSONParser]
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
