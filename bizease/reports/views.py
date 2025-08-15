from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from inventory.models import Inventory
from orders.models import Order, OrderedProduct
from django.db.models import Sum, F
from rest_framework import status
from django.utils  import timezone
from datetime import timedelta, datetime


def process_GET_parameters(request):
    user = request.user
    start_date = None
    end_date = None

    valid_values  = ["last-week", "last-month", "last-6-months", "last-year"]

    period = request.GET.get('period')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if period and (start_date or end_date):
        return {"error": "Invalid GET parameters. Only period or a combination of start_date and end_date is allowed"}

    if period and len(request.GET.getlist('period')) == 1:
        if period not in valid_values:
            return {"error": "Invalid value for period parameter"}

        # 181 days was used for 6 months because not all months have 30 days 
        # so an extra day was added to be just a little bit more accurate
        date_range_to_days_map = {"last-week": 7, "last-month": 30, "last-6-months": 181, "last-year": 365}
        days_num = date_range_to_days_map[period]
        current_timestamp = timezone.now()
        start_date = (current_timestamp - timedelta(days=days_num)).date()
        end_date = current_timestamp.date()
        return {"start_date": start_date, "end_date": end_date, "time_period": period}

    elif start_date_str and (len(request.GET.getlist('start_date')) == 1) and end_date_str and (len(request.GET.getlist('end_date')) == 1):
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            return {"error": "Invalid date format. Use YYYY-MM-DD"}
        else:
            return {"start_date": start_date, "end_date": end_date, "time_period": f"{start_date} to {end_date}"}

    return {} 



class ReportDataView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, **kwargs):
        range_dict = process_GET_parameters(self.request)
        if (range_dict.get("error")):
            return Response({"detail": range_dict["error"]}, status=status.HTTP_400_BAD_REQUEST)
            
        start_date = range_dict.get("start_date")
        end_date = range_dict.get("end_date")

        report_data = {}
        report_data["total_products"] = Inventory.objects.filter(owner=request.user.id).count()
        report_data["low_stock_items"] = Inventory.objects.filter(owner=request.user.id).filter(stock_level__lte=F("low_stock_threshold")).count()

        period = self.request.GET.get('period')
        if not start_date and not end_date:
            report_data["period"] = "All time"

            top_product = (
                OrderedProduct.objects
                .filter(order_id__product_owner_id=request.user)
                .values("name")
                .annotate(total_sold=Sum("quantity"))
                .order_by("-total_sold")
                .first()
            )
            report_data["top_selling_product"] = top_product["name"] if top_product else None
            report_data["pending_orders"] = Order.objects.filter(product_owner_id=request.user.id).filter(status="Pending").count()
            report_data["total_stock_value"] = Inventory.objects.filter(owner=request.user.id).annotate(value=F("price")*F("stock_level")).aggregate(Sum("value"))["value__sum"]
            report_data["stock_value_change"] = None
            if report_data["total_stock_value"] is None:
                report_data["total_stock_value"] = 0

            report_data["total_revenue"] = (
                Order.objects.filter(product_owner_id=request.user.id).filter(status="Delivered").aggregate(Sum("total_price"))["total_price__sum"]
            )
            if report_data["total_revenue"] is None:
                report_data["total_revenue"] = 0
            report_data["revenue_change"] = None

            date_revenue_chart_data = (
                Order.objects.filter(product_owner_id=request.user.id).filter(status="Delivered").values("order_date")
                .annotate(date=F("order_date"), revenue=Sum("total_price")).order_by("-order_date").values("date", "revenue")
            )
            report_data["date_revenue_chart_data"] = date_revenue_chart_data
            product_sales_chart_data = OrderedProduct.objects.filter(order_id__product_owner_id=request.user.id).filter(order_id__status="Delivered").values('name').annotate(quantity_sold=Sum("quantity"))
            report_data["product_sales_chart_data"] = product_sales_chart_data
        else:
            report_data["period"] = range_dict["time_period"]
            top_product = (
                OrderedProduct.objects
                .filter(order_id__product_owner_id=request.user.id)
                .filter(order_id__order_date__range=(start_date, end_date))
                .filter(order_id__status="Delivered")
                .values("name")
                .annotate(total_sold=Sum("quantity"))
                .order_by("-total_sold")
                .first()
            )
            report_data["top_selling_product"] = top_product["name"] if top_product else None
            
            report_data["pending_orders"] = (
                Order.objects.filter(product_owner_id=request.user.id)
                .filter(order_date__range=(start_date, end_date))
                .filter(status="Pending").count()
            )

            prev_period_offsets = {"last-week": 8, "last-month": 31, "last-6-months": 182, "last-year": 366}
            prev_cutoff_date = start_date - timedelta(days=prev_period_offsets[period])

            cutoff_date = end_date
            report_data["total_stock_value"] = (
                Inventory.objects.filter(owner=request.user.id).filter(date_added__lte=cutoff_date).annotate(value=F("price")*F("stock_level")).aggregate(Sum("value"))["value__sum"]
            )
            prev_period_stock_value = (
                Inventory.objects.filter(owner=request.user.id).filter(date_added__lte=prev_cutoff_date).annotate(value=F("price")*F("stock_level")).aggregate(Sum("value"))["value__sum"]
            )

            if (report_data["total_stock_value"] is None):
                report_data["total_stock_value"] = 0
            if prev_period_stock_value is None:
                prev_period_stock_value = 0

            change = report_data["total_stock_value"] - prev_period_stock_value
            if prev_period_stock_value == 0:
                change_percentage = None
            else:
                change_percentage = round((change/prev_period_stock_value) * 100, 2)

            report_data["stock_value_change"] = change_percentage

            report_data["total_revenue"] = (
                Order.objects.filter(product_owner_id=request.user.id)
                .filter(order_date__range=(start_date, end_date))
                .filter(status="Delivered")
                .aggregate(Sum("total_price"))["total_price__sum"]
            )

            prev_start_date = start_date - timedelta(days=prev_period_offsets[period])
            prev_end_date = start_date - timedelta(days=1)

            prev_revenue = (
                Order.objects
                .filter(product_owner_id=request.user.id)
                .filter(order_date__range=(prev_start_date, prev_end_date))
                .filter(status="Delivered")
                .aggregate(Sum("total_price"))['total_price__sum']
            )

            if (report_data["total_revenue"] is None):
                report_data["total_revenue"] = 0
            if prev_revenue is None:
                prev_revenue = 0

            change = report_data["total_revenue"] - prev_revenue
            if prev_revenue == 0:
                change_percentage = None
            else:
                change_percentage = round((change/prev_revenue) * 100, 2)

            report_data["revenue_change"] = change_percentage

            date_revenue_chart_data = (
                Order.objects
                .filter(product_owner_id=request.user.id)
                .filter(order_date__range=(start_date, end_date))
                .filter(status="Delivered")
                .annotate(revenue=Sum("total_price"), date=F("order_date")).values("date", "revenue")
            )
            report_data["date_revenue_chart_data"] = date_revenue_chart_data
            product_sales_chart_data = (
                OrderedProduct.objects
                .filter(order_id__product_owner_id=request.user.id)
                .filter(order_id__order_date__range=(start_date, end_date))
                .filter(order_id__status="Delivered")
                .values('name').annotate(quantity_sold=Sum("quantity"))
            )
            report_data["product_sales_chart_data"] = product_sales_chart_data

        return Response({"data": report_data}, status=status.HTTP_200_OK)

class ReportDataSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, **kwargs):
        range_dict = process_GET_parameters(self.request)
        if (range_dict.get("error")):
            return Response({"detail": range_dict["error"]}, status=status.HTTP_400_BAD_REQUEST)

        start_date = range_dict.get("start_date")
        end_date = range_dict.get("end_date")

        if not start_date and not end_date:
            summary = (
                OrderedProduct.objects
                .filter(order_id__product_owner_id=request.user.id)
                .filter(order_id__status="Delivered")
                .order_by("name").values('name')
                .annotate(quantity_sold=Sum("quantity"), revenue=Sum("cummulative_price"))
            )
        else:
            summary = (
                OrderedProduct.objects
                .filter(order_id__product_owner_id=request.user.id)
                .filter(order_id__order_date__range=(start_date, end_date))
                .filter(order_id__status="Delivered")
                .order_by("name").values('name')
                .annotate(quantity_sold=Sum("quantity"), revenue=Sum("cummulative_price"))
            )

        inventory_items = Inventory.objects.filter(owner=request.user.id).filter(owner=self.request.user).order_by("product_name")

        for obj in summary:
            for item in inventory_items:
                if obj["name"] == item.product_name:
                    obj["stock_status"] = "low stock" if item.stock_level < item.low_stock_threshold else "in stock"
                    
            if not obj.get("stock_status"):
                obj["stock_status"] = "out of stock"

        time_period = "All time" if not range_dict.get("time_period") else range_dict["time_period"]
        return Response({"data": {"summary": summary, "period": time_period}}, status=status.HTTP_200_OK)

