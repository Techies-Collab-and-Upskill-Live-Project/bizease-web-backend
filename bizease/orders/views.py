from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from .serializers import OrderSerializer
from rest_framework.response import Response
from .models import Order
from rest_framework import status
from django.db.models import Sum, F


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

	# To implement: filter, search and normal get
	def get(self, request, **kwargs):
		# Tell frontend that id is order_id and they should reformat it to look fancy or whatever
		serializer = OrderSerializer(list(Order.objects.all()), many=True)
		return Response({"data": serializer.data}, status=status.HTTP_200_OK)

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
			return Response(response["details"], status=response["status"])
		else:
			return Response({"detail": order_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

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
