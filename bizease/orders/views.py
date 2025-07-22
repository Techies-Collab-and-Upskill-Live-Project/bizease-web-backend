from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView
from .serializers import OrderSerializer, OrderedProductSerializer
from rest_framework.response import Response
from .models import Order, OrderedProduct
from rest_framework import status
from django.db.models import Sum, F, Q
import math


class OrderStatsView(APIView):
	permission_classes = [IsAuthenticated]
	parser_classes = [JSONParser]

	def get(self, request, **kwargs):
		data = {
			"total_orders": Order.objects.filter(product_owner_id=request.user.id).count(),
			"total_revenue": Order.objects.filter(product_owner_id=request.user.id).filter(status="Delivered").aggregate(Sum("total_price"))['total_price__sum'],
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
		return Response({"data": data}, status=status.HTTP_200_OK)

	def post(self, request, **kwargs):
		order_serializer = OrderSerializer(data=request.data)
		if order_serializer.is_valid():
			response = order_serializer.save(request.user)
			errors = response.get("errors")
			if not errors:
				return Response(
					{
						"detail": "Order created successfully",
						"data": OrderSerializer(response["data"]).data
					}, status=status.HTTP_201_CREATED
				)

			elif (errors == "Fatal error"):
				return Response({"detail": "Something went wrong! Please try again"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
			else:
				return Response({"detail": errors}, status=status.HTTP_400_BAD_REQUEST)	
		else:
			return Response({"detail": order_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class SingleOrderView(APIView):
	parser_classes = [JSONParser]
	permission_classes = [IsAuthenticated]

	def get(self, request, order_id, **kwargs):
		try:
			item = Order.objects.filter(product_owner_id=request.user.id).get(pk=order_id)
		except Order.DoesNotExist:
			return Response({"detail": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
		except Order.MultipleObjectsReturned: # This shouldn't be possible but it's handled anyways
			return Response({"detail": "Something went wrong! Please try again"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
		return Response({"data": OrderSerializer(item).data}, status=status.HTTP_200_OK)

	def put(self, request, order_id, **kwargs):
		try:
			order_to_edit = Order.objects.filter(product_owner_id=request.user.id).get(pk=order_id)
		except Order.DoesNotExist:
			return Response({"detail": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
		except Order.MultipleObjectsReturned: # This shouldn't be possible but it's handled anyways
			return Response({"detail": "Something went wrong! Please try again"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
		order_edits = OrderSerializer(order_to_edit, data=request.data, partial=True)

		if order_edits.is_valid():
			response = order_edits.save(request.user)
			if (response.get("errors")):
				status_code = status.HTTP_500_INTERNAL_SERVER_ERROR if update_results["errors"] == "Fatal error" else status.HTTP_400_BAD_REQUEST
				return Response({"detail": response["errors"]}, status=status.status_code)
			return Response(
				{
					"detail": "Order created successfully",
					"data": OrderSerializer(response["data"]).data
				}, status=status.HTTP_200_OK
			)
		else:
			return Response({"detail": order_edits.errors}, status=status.HTTP_400_BAD_REQUEST)

	def delete(self, request, order_id, **kwargs):
		try:
			item = Order.objects.filter(product_owner_id=request.user.id).get(pk=order_id)
		except Order.DoesNotExist:
			return Response({"detail": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
		except Order.MultipleObjectsReturned: # This shouldn't be possible but it's handled anyways
			return Response({"detail": "Something went wrong! Please try again"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

		if (item.status == "Delivered"):
			return Response({"detail": "Only Pending orders can be deleted"}, status=status.HTTP_400_BAD_REQUEST)

		del_count, del_dict = item.delete()
		if (del_count > 0):
			return Response({"detail": "Order deleted successfully"}, status=status.HTTP_200_OK)
		else: # What could go wrong?
			return Response(
				{"detail": "Delete operation incomplete. Something went wrong while deleting Order"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
			)

class OrderedProductsView(APIView):
	parser_classes = [JSONParser]
	permission_classes = [IsAuthenticated]

	def post(self, request, order_id, **kwargs):
		try:
			order = Order.objects.filter(product_owner_id=request.user.id).get(pk=order_id)
		except Order.DoesNotExist:
			return Response({"detail": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

		ordered_product_serializer = OrderedProductSerializer(data=request.data)
		if (ordered_product_serializer.is_valid()):
			save_results = ordered_product_serializer.save(order)
			if save_results.get("errors"):
				return Response({"detail": save_results["errors"]}, status=status.HTTP_400_BAD_REQUEST)
			return Response({"detail": "product added to Order successfully"}, status=status.HTTP_201_CREATED)
		else:
			return Response({"detail": ordered_product_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class SingleOrderedProductView(APIView):
	parser_classes = [JSONParser]
	permission_classes = [IsAuthenticated]

	def get(self, request, order_id, product_id, **kwargs):
		try:
			order = Order.objects.filter(product_owner_id=request.user.id).get(pk=order_id)
			product = order.ordered_products.get(pk=product_id)
		except Order.DoesNotExist:
			return Response({"detail": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
		except OrderedProduct.DoesNotExist:
			return Response({"detail": "Ordered Product not found"}, status=status.HTTP_404_NOT_FOUND)
		except (Order.MultipleObjectsReturned, OrderedProduct.MultipleObjectsReturned): # This shouldn't be possible but it's handled anyways
			return Response({"detail": "Something went wrong! Please try again"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
		return Response({"data": OrderedProductSerializer(product).data}, status=status.HTTP_200_OK)

	def put(self, request, order_id, product_id, **kwargs):
		try:
			order = Order.objects.filter(product_owner_id=request.user.id).get(pk=order_id)
			product = order.ordered_products.get(pk=product_id)
		except Order.DoesNotExist:
			return Response({"detail": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
		except OrderedProduct.DoesNotExist:
			return Response({"detail": "Ordered Product not found"}, status=status.HTTP_404_NOT_FOUND)
		except (Order.MultipleObjectsReturned, OrderedProduct.MultipleObjectsReturned): # This shouldn't be possible but it's handled anyways
			return Response({"data": "Something went wrong! Please try again"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
		product_edit = OrderedProductSerializer(product, data=request.data, partial=True)

		if product_edit.is_valid():
			update_results = product_edit.save()
			if update_results.get("errors"):
				return Response({"detail": update_results["errors"]}, status=status.HTTP_400_BAD_REQUEST)
			return Response({"detail": OrderedProductSerializer(update_results["data"]).data}, status=status.HTTP_200_OK)
		else:
			return Response({"detail": product_edit.errors}, status=status.HTTP_400_BAD_REQUEST)

	def delete(self, request, order_id, product_id, **kwargs):
		try:
			item = Order.objects.filter(product_owner_id=request.user.id).get(pk=order_id)
			product = item.ordered_products.get(pk=product_id)
		except Order.DoesNotExist:
			return Response({"detail": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
		except OrderedProduct.DoesNotExist:
			return Response({"detail": "Ordered Product not found"}, status=status.HTTP_404_NOT_FOUND)
		except (Order.MultipleObjectsReturned, OrderedProduct.MultipleObjectsReturned): # This shouldn't be possible but it's handled anyways
			return Response({"detail": "Something went wrong! Please try again"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

		if (item.status == "Delivered"):
			return Response({"detail": "Only the Ordered products of Pending Orders can be deleted"}, status=status.HTTP_400_BAD_REQUEST)
		if item.ordered_products.count() == 1:
			return Response(
				{"detail": "The only ordered product of an order can't be deleted. An Order must have at least one ordered product"},
				status=status.HTTP_400_BAD_REQUEST
			)

		del_count, del_dict = item.delete()
		if (del_count > 0):
			return Response({"detail": "Ordered product deleted successfully"}, status=status.HTTP_200_OK)
		else: # What could go wrong?
			return Response(
				{"detail": "Delete operation incomplete. Something went wrong while deleting Order"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
			)