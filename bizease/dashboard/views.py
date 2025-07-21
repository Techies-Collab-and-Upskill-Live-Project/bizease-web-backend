from rest_framework.response import Response
from rest_framework.views import APIView
from orders.models import Order, OrderedProduct
from inventory.models import Inventory
from rest_framework import status
from django.db.models import Sum, F
from orders.serializers import OrderSerializer
from inventory.serializers import InventoryItemSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser
from datetime import timedelta, datetime


class DashBoardView(APIView):
    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]

    def get(self, request, **kwargs):
        dashboard_data = {}
        dashboard_data["business_name"] = request.user.business_name
        dashboard_data["currency"] = request.user.currency
        dashboard_data["language"] = request.user.language

        period = request.GET.get('period')

        if period and (len(request.GET.getlist('period')) == 1) and period == "all-time":
            # should it be filtered over delivered products or not
            products_orders = OrderedProduct.objects.filter(order_id__product_owner_id=request.user.id).values("name").annotate(total_units_sold=Sum("quantity")).order_by("-total_units_sold")

            # top selling product - ordered product with the max sum of quantity
            if len(products_orders) == 0:
                dashboard_data["top_selling_product"] = None
            else:
                dashboard_data["top_selling_product"] = products_orders[0]['name']

            # revenue - sum of total_price in orders
            dashboard_data["revenue"] = Order.objects.filter(product_owner_id=request.user.id).aggregate(Sum("total_price"))['total_price__sum']

            orders_serializer = OrderSerializer(
                list(Order.objects.filter(product_owner_id=request.user.id).filter(status="Pending").order_by("-order_date")[:6]),
                many=True
            )
            inventory_serializer = InventoryItemSerializer(
                list(Inventory.objects.filter(owner=request.user.id).filter(stock_level__lte=F("low_stock_threshold")).order_by("-last_updated")[:6]),
                many=True
            )
            dashboard_data["pending_orders"] = orders_serializer.data
            dashboard_data["low_stock_items"] = inventory_serializer.data
            return Response({"data": dashboard_data}, status=status.HTTP_200_OK)

        else: # get last 30 days dashboard data
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)

            products_orders = (
                OrderedProduct.objects.filter(order_id__order_date__range=(start_date, end_date))
                .filter(order_id__product_owner_id=request.user.id)
                .values("name").annotate(total_units_sold=Sum("quantity"))
                .order_by("-total_units_sold")
            )

            # top selling product - ordered product with the max sum of quantity
            if len(products_orders) == 0:
                dashboard_data["top_selling_product"] = None
            else:
                dashboard_data["top_selling_product"] = products_orders[0]['name']

            # revenue - sum of total_price in orders
            dashboard_data["revenue"] = Order.objects.filter(order_date__range=(start_date, end_date)).filter(product_owner_id=request.user.id).aggregate(Sum("total_price"))['total_price__sum']

            orders_serializer = OrderSerializer(
                list(Order.objects.filter(product_owner_id=request.user.id).filter(order_date__range=(start_date, end_date)).filter(status="Pending").order_by("-order_date")[:6]),
                many=True
            )
            inventory_serializer = InventoryItemSerializer(
                list(Inventory.objects.filter(owner=request.user.id).filter(stock_level__lte=F("low_stock_threshold")).order_by("-last_updated")[:6]),
                many=True
            )
            dashboard_data["pending_orders"] = orders_serializer.data
            dashboard_data["low_stock_items"] = inventory_serializer.data
            return Response({"data": dashboard_data}, status=status.HTTP_200_OK)
