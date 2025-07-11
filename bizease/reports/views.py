from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from inventory.models import Inventory
from orders.models import Order, OrderedProduct
from django.db.models import Sum, F, Q
from rest_framework import status
from datetime import datetime

class ReportsOverview(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, **kwargs):
        user = request.user
        report_data = {}

        #  Top Selling Product
        top_product = (
            OrderedProduct.objects
            .filter(order_id__product_owner_id=user)
            .values("name")
            .annotate(total_sold=Sum("quantity"))
            .order_by("-total_sold")
            .first()
        )
        report_data["top_product"] = top_product["name"] if top_product else None

        #  Low Stock Alerts
        low_stock_items = Inventory.objects.filter(
            owner=user,
            stock_level__lte=F("low_stock_threshold")
        ).values("product_name", "stock_level", "low_stock_threshold")
        report_data["low_stock_items"] = list(low_stock_items)

        #  Products with No Sales
        sold_product_names = OrderedProduct.objects.filter(
            order_id__product_owner_id=user
        ).values_list("name", flat=True).distinct()

        no_sales_items = Inventory.objects.filter(
            owner=user
        ).exclude(product_name__in=sold_product_names).values("product_name", "stock_level")
        report_data["unsold_products"] = list(no_sales_items)

        #  Product Sales Summary Table
        product_sales = (
            OrderedProduct.objects
            .filter(order_id__product_owner_id=user)
            .values("name")
            .annotate(
                total_units_sold=Sum("quantity"),
                total_price_earned=Sum("cummulative_price"),
            )
        )

        inventory_data = Inventory.objects.filter(owner=user).values("product_name", "stock_level")
        availability = {item["product_name"]: item["stock_level"] > 0 for item in inventory_data}

        summary_table = []
        for p in product_sales:
            summary_table.append({
                "product_name": p["name"],
                "units_sold": p["total_units_sold"],
                "total_earned": p["total_price_earned"],
                "available": availability.get(p["name"], False)
            })

        report_data["product_sales_summary"] = summary_table

        return Response({"data": report_data}, status=status.HTTP_200_OK)

class RevenueReportByDate(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, **kwargs):
        user = request.user
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        if not start_date or not end_date:
            return Response({"detail": "Both start_date and end_date are required"}, status=400)

        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            return Response({"detail": "Invalid date format. Use YYYY-MM-DD"}, status=400)

        filtered_orders = Order.objects.filter(
            product_owner_id=user,
            order_date__range=(start, end)
        )

        total_orders = filtered_orders.count()
        total_revenue = filtered_orders.aggregate(Sum("total_price"))["total_price__sum"] or 0

        return Response({
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "currency": user.currency
        }, status=200)

