from django.urls import path
from .views import ReportDataView, ReportDataSummaryView


urlpatterns = [
    path('', ReportDataView.as_view(), name='reports'),
    path('summary', ReportDataSummaryView.as_view(), name='reports-summary')
]
