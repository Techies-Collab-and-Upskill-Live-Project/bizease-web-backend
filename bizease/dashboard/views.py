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

        try:
            period_date = datetime.strptime(period, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            # "Invalid date format. Use YYYY-MM-DD"
            period_date = None

        if period_date:
            prev_date = period_date - timedelta(days=1)

            products_orders = (
                OrderedProduct.objects
                .filter(order_id__product_owner_id=request.user.id)
                .filter(order_id__order_date=(period_date))
                .filter(order_id__status="Delivered")
                .values("name").annotate(total_units_sold=Sum("quantity"))
                .order_by("-total_units_sold")
            )

            # top selling product - ordered product with the max sum of quantity
            if len(products_orders) == 0:
                dashboard_data["top_selling_product"] = None
            else:
                dashboard_data["top_selling_product"] = products_orders[0]['name']

            prev_revenue = (
                Order.objects
                .filter(product_owner_id=request.user.id)
                .filter(order_date=(prev_date))
                .filter(status="Delivered")
                .aggregate(Sum("total_price"))['total_price__sum']
            )

            # revenue - sum of total_price in orders
            dashboard_data["revenue"] = (
                Order.objects
                .filter(product_owner_id=request.user.id)
                .filter(order_date=(period_date))
                .filter(status="Delivered")
                .aggregate(Sum("total_price"))['total_price__sum']
            )

            if (dashboard_data["revenue"] is None):
                dashboard_data["revenue"] = 0
            if prev_revenue is None:
                prev_revenue = 0

            change = dashboard_data["revenue"] - prev_revenue
            if prev_revenue == 0:
                change_percentage = None
            else:
                change_percentage = round((change/prev_revenue) * 100, 2)

            dashboard_data["revenue_change"] = change_percentage

            orders_serializer = OrderSerializer(
                list(
                    Order.objects
                    .filter(product_owner_id=request.user.id)
                    .filter(order_date=(period_date))
                    .filter(status="Pending")
                    .order_by("-order_date")[:6]
                ),
                many=True
            )
            inventory_serializer = InventoryItemSerializer(
                list(Inventory.objects.filter(owner=request.user.id).filter(stock_level__lte=F("low_stock_threshold")).order_by("-last_updated")[:6]),
                many=True
            )
            dashboard_data["pending_orders"] = orders_serializer.data
            dashboard_data["low_stock_items"] = inventory_serializer.data
            return Response({"data": dashboard_data}, status=status.HTTP_200_OK)

        elif period and (len(request.GET.getlist('period')) == 1) and period == "all-time":

            products_orders = (
                OrderedProduct.objects
                .filter(order_id__product_owner_id=request.user.id)
                .filter(order_id__status="Delivered").values("name")
                .annotate(total_units_sold=Sum("quantity")).order_by("-total_units_sold")
            )

            # top selling product - ordered product with the max sum of quantity
            if len(products_orders) == 0:
                dashboard_data["top_selling_product"] = None
            else:
                dashboard_data["top_selling_product"] = products_orders[0]['name']

            # revenue - sum of total_price in orders
            dashboard_data["revenue"] = (
                Order.objects.filter(product_owner_id=request.user.id).filter(status="Delivered").aggregate(Sum("total_price"))['total_price__sum']
            )
            dashboard_data["revenue_change"] = None

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

            prev_start_date = start_date - timedelta(days=31)
            prev_end_date = start_date - timedelta(days=1)

            products_orders = (
                OrderedProduct.objects
                .filter(order_id__product_owner_id=request.user.id)
                .filter(order_id__order_date__range=(start_date, end_date))
                .filter(order_id__status="Delivered")
                .values("name").annotate(total_units_sold=Sum("quantity"))
                .order_by("-total_units_sold")
            )

            # top selling product - ordered product with the max sum of quantity
            if len(products_orders) == 0:
                dashboard_data["top_selling_product"] = None
            else:
                dashboard_data["top_selling_product"] = products_orders[0]['name']

            prev_revenue = (
                Order.objects
                .filter(product_owner_id=request.user.id)
                .filter(order_date__range=(prev_start_date, prev_end_date))
                .filter(status="Delivered")
                .aggregate(Sum("total_price"))['total_price__sum']
            )

            # revenue - sum of total_price in orders
            dashboard_data["revenue"] = (
                Order.objects
                .filter(product_owner_id=request.user.id)
                .filter(order_date__range=(start_date, end_date))
                .filter(status="Delivered")
                .aggregate(Sum("total_price"))['total_price__sum']
            )

            if (dashboard_data["revenue"] is None):
                dashboard_data["revenue"] = 0
            if prev_revenue is None:
                prev_revenue = 0

            change = dashboard_data["revenue"] - prev_revenue
            if prev_revenue == 0:
                change_percentage = None
            else:
                change_percentage = round((change/prev_revenue) * 100, 2)

            dashboard_data["revenue_change"] = change_percentage

            orders_serializer = OrderSerializer(
                list(
                    Order.objects
                    .filter(product_owner_id=request.user.id)
                    .filter(order_date__range=(start_date, end_date))
                    .filter(status="Pending")
                    .order_by("-order_date")[:6]
                ),
                many=True
            )
            inventory_serializer = InventoryItemSerializer(
                list(Inventory.objects.filter(owner=request.user.id).filter(stock_level__lte=F("low_stock_threshold")).order_by("-last_updated")[:6]),
                many=True
            )
            dashboard_data["pending_orders"] = orders_serializer.data
            dashboard_data["low_stock_items"] = inventory_serializer.data
            return Response({"data": dashboard_data}, status=status.HTTP_200_OK)
