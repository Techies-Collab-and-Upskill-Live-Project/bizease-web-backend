from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from .serializers import OrderSerializer, ProductsOrdersSerializers
from rest_framework.response import Response
from django.db.models import Model
from .models import Order
from rest_framework import status

def get_objects_by_pk_or_errobj(model, target_pk):
	try:
		item = model.objects.get(pk=target_pk)
	except Model.DoesNotExist:
		return {"msg": "Item not found", "status": status.HTTP_404_NOT_FOUND},
	except Model.MultipleObjectsReturned: # This shouldn't be possible but it's handled anyways
		return {"msg": "Target happens to be multiple items", "status": status.HTTP_500_INTERNAL_SERVER_ERROR}
	return {"obj": item}


class OrdersView(APIView):
	permission_classes = [IsAuthenticated]

	# To implement: filter (by category, status, stock_level), search and normal get
	def get(self, request, **kwargs):
		# Tell frontend that id is order_id and they should reformat it to look fancy or whatever
		serializer = ProductsOrdersSerializers({"data": list(Order.objects.all())})
		return Response(serializer.data, status=status.HTTP_200_OK)

	def post(self, request, **kwargs):
		order_serializer = OrderSerializer(data=request.data)
		if order_serializer.is_valid():
			response = order_serializer.save(request.user)
			return Response(response["details"], status=response["status"])
		else:
			return Response({"errors": order_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class SingleOrderView(APIView):
	def get(self, request, itemId, **kwargs):
		# Tell frontend that id is order_id and they should reformat it to look fancy or whatever
		data = ProductsOrdersSerializers(data={"entries": Orders.objects.all()}).data
		return Response({"data": data}, status=status.HTTP_200_OK)

	# def put(self, request, itemId, **kwargs):
	# 	result = get_objects_by_pk_or_errobj(Inventory, itemId)
	# 	if not result.get("obj"):
	# 		return Response({"msg": result["msg"]}, status=result["status"])
	# 	order_edits = OrderSerializer(result["obj"], data=request.data, partial=True)

	# 	if order_edits.is_valid():
	# 		response = order_edits.save()
	# 		return Response(response["details"], status=response["status"])
	# 	else:
	# 		return Response({"errors": order_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

	def delete(self, request, itemId, **kwargs):
		try:
			item = Inventory.objects.get(pk=itemId)
		except Model.DoesNotExist:
			return Response({"msg": "Item not found"}, status=status.HTTP_404_NOT_FOUND)
		except Model.MultipleObjectsReturned: # This shouldn't be possible but it's handled anyways
			return Response({"msg": "Target happens to be multiple items"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

		del_count, del_dict = item.delete()
		if (del_count > 0):
			return Response({"msg": "Order deleted successfully"}, status=status.HTTP_200_OK)
		else: # What could go wrong?
			return Response(
				{"msg": "Delete operation incomplete. Something went wrong while deleting inventory Item"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
			)
