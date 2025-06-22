from django.urls import path
from .views import DashboardView
from .views import ReportListCreateView, ReportDetailView


urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('reports/', ReportListCreateView.as_view(), name='create-list-reports'),
    path('reports/<int:pk>/', ReportDetailView.as_view(), name='detail-report'),
    path('reports/<int:pk>/download/', ReportDownloadView.as_view(), name='report-download')
]
